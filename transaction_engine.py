"""
Transaction Engine
Double-entry logic, account statements, budget envelope tracking,
macro workflow execution, and cycle analytics.
"""

from datetime import date, datetime
import pandas as pd
import config
from cycle_utils import get_cycle_for_date, get_current_cycle_info, calculate_food_burn_metrics
from backend import FinanceBackend

class TransactionEngine:
    def __init__(self, backend: FinanceBackend):
        self.backend = backend

    def get_accounts_summary(self) -> dict:
        """
        Returns summary of all 4 accounts, total net worth, and account breakdown.
        """
        accounts = self.backend.get_accounts()
        acc_dict = {a["Account_Name"]: a for a in accounts}
        
        # Ensure all 4 core accounts are present
        res = {}
        total_net_worth = 0.0
        for name, meta in config.ACCOUNTS.items():
            acc_data = acc_dict.get(name, {})
            current_bal = float(acc_data.get("Current_Balance", meta["default_initial"]))
            initial_bal = float(acc_data.get("Initial_Balance", meta["default_initial"]))
            total_net_worth += current_bal
            res[name] = {
                "name": name,
                "display_name": meta["name"],
                "role": meta["role"],
                "type": meta["type"],
                "icon": meta["icon"],
                "color": meta["color"],
                "initial_balance": initial_bal,
                "current_balance": current_bal,
                "updated_at": acc_data.get("Updated_At", "-")
            }
            
        thai_credit_bal = res.get("Thai Credit", {}).get("current_balance", 0.0)
        scb_bal = res.get("SCB", {}).get("current_balance", 0.0)
        kbank_bal = res.get("KBANK", {}).get("current_balance", 0.0)
        bay_bal = res.get("BAY", {}).get("current_balance", 0.0)
        active_liquidity = thai_credit_bal + scb_bal

        return {
            "accounts": res,
            "total_net_worth": total_net_worth,
            "active_liquidity": active_liquidity,
            "thai_credit_balance": thai_credit_bal,
            "scb_balance": scb_bal,
            "kbank_balance": kbank_bal,
            "bay_balance": bay_bal,
        }

    def get_cycle_analytics(self, cycle_id: str | None = None) -> dict:
        """
        Analyzes spending, envelopes, burn rate, and meal counters for a specific cycle.
        """
        current_cycle = get_current_cycle_info()
        target_cycle_id = cycle_id or current_cycle["cycle_id"]

        transactions = self.backend.get_transactions()
        df = pd.DataFrame(transactions)

        if df.empty:
            df = pd.DataFrame(columns=["Transaction_ID", "Date", "Cycle", "Type", "From_Account", "To_Account", "Category", "Amount", "Note"])

        cycle_df = df[df["Cycle"] == target_cycle_id] if not df.empty and "Cycle" in df.columns else pd.DataFrame()

        # Category spending aggregation
        cat_spend = {cat: 0.0 for cat in config.CATEGORY_NAMES}
        if not cycle_df.empty:
            expenses = cycle_df[cycle_df["Type"] == "Expense"]
            for _, row in expenses.iterrows():
                cat = row.get("Category")
                amt = float(row.get("Amount", 0.0))
                if cat in cat_spend:
                    cat_spend[cat] += amt
                else:
                    cat_spend[cat] = amt

        # Daily Food Metrics
        food_spent = cat_spend.get("Food_Daily", 0.0)
        food_metrics = calculate_food_burn_metrics(food_spent, current_cycle)

        # Special Meal Counter
        special_meals_df = cycle_df[(cycle_df["Type"] == "Expense") & (cycle_df["Category"] == "Special_Meal")] if not cycle_df.empty else pd.DataFrame()
        special_meals_count = len(special_meals_df)
        special_meals_spent = cat_spend.get("Special_Meal", 0.0)
        special_meal_max = config.BUDGET_RULES["Daily Living (SCB Weekly Disbursed)"]["Special Meals Max Count"]

        # Fixed Commitments tracking
        fixed_status = {
            "Mom": {"budget": 5000.0, "spent": cat_spend.get("Mom", 0.0), "done": cat_spend.get("Mom", 0.0) >= 5000.0},
            "DCA": {"budget": 4800.0, "spent": cat_spend.get("DCA", 0.0), "done": cat_spend.get("DCA", 0.0) >= 4800.0},
            "Rent": {"budget": 6000.0, "spent": cat_spend.get("Rent", 0.0), "done": cat_spend.get("Rent", 0.0) >= 6000.0},
            "Utilities_Phone": {"budget": 2650.0, "spent": cat_spend.get("Utilities_Phone", 0.0), "done": cat_spend.get("Utilities_Phone", 0.0) >= 2650.0},
        }

        # Insurance Sinking Fund Transfer check (Thai Credit -> BAY)
        insurance_transfers = cycle_df[(cycle_df["Type"] == "Internal_Transfer") & (cycle_df["From_Account"] == "Thai Credit") & (cycle_df["To_Account"] == "BAY")] if not cycle_df.empty else pd.DataFrame()
        insurance_funded = float(insurance_transfers["Amount"].sum()) if not insurance_transfers.empty else 0.0
        insurance_status = {"budget": 3500.0, "funded": insurance_funded, "done": insurance_funded >= 3500.0}

        # Total Cycle Income & Total Expense
        total_income = float(cycle_df[(cycle_df["Type"] == "Income") & (cycle_df["Category"] == "Salary")]["Amount"].sum()) if not cycle_df.empty else 0.0
        total_expense = float(cycle_df[cycle_df["Type"] == "Expense"]["Amount"].sum()) if not cycle_df.empty else 0.0

        return {
            "cycle_info": current_cycle,
            "category_spend": cat_spend,
            "food_metrics": food_metrics,
            "special_meals_count": special_meals_count,
            "special_meals_spent": special_meals_spent,
            "special_meal_max": special_meal_max,
            "fixed_status": fixed_status,
            "insurance_status": insurance_status,
            "total_income": total_income,
            "total_expense": total_expense,
            "cycle_transactions_count": len(cycle_df)
        }

    def get_account_statement(self, account_name: str) -> pd.DataFrame:
        """
        Returns full statement with Running Balance for the specified bank account.
        """
        accounts = self.backend.get_accounts()
        initial_bal = 0.0
        for acc in accounts:
            if acc["Account_Name"] == account_name:
                initial_bal = float(acc.get("Initial_Balance", 0.0))
                break

        transactions = self.backend.get_transactions()
        if not transactions:
            return pd.DataFrame(columns=["Date", "Transaction_ID", "Type", "Description", "Inflow", "Outflow", "Balance", "Category", "Note"])

        df = pd.DataFrame(transactions)
        # Sort chronologically
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values(by=["Date", "Transaction_ID"], ascending=True)

        rows = []
        running_bal = initial_bal
        
        # Initial balance row
        rows.append({
            "Date": df["Date"].min().strftime("%Y-%m-%d") if not df.empty else date.today().strftime("%Y-%m-%d"),
            "Transaction_ID": "INITIAL",
            "Type": "Initial Balance",
            "Description": f"🏁 ยอดเงินเริ่มต้น / ยกมา ({account_name})",
            "Inflow": initial_bal,
            "Outflow": 0.0,
            "Balance": running_bal,
            "Category": "Initial_Balance",
            "Note": "Starting Balance Setup"
        })

        for _, tx in df.iterrows():
            tx_type = tx.get("Type")
            from_acc = tx.get("From_Account")
            to_acc = tx.get("To_Account")
            amount = float(tx.get("Amount", 0.0))
            cat = tx.get("Category", "")
            note = tx.get("Note", "")
            tx_id = tx.get("Transaction_ID", "")
            tx_date_str = tx["Date"].strftime("%Y-%m-%d")

            inflow = 0.0
            outflow = 0.0
            desc = ""

            if tx_type == "Expense" and from_acc == account_name:
                outflow = amount
                running_bal -= amount
                desc = f"โอนจ่ายค่า {config.CATEGORIES.get(cat, {}).get('label', cat)}"
            elif tx_type == "Internal_Transfer":
                if from_acc == account_name:
                    outflow = amount
                    running_bal -= amount
                    desc = f"โอนออกไปยัง ➡️ {to_acc}"
                elif to_acc == account_name:
                    inflow = amount
                    running_bal += amount
                    desc = f"โอนเข้าจาก ⬅️ {from_acc}"
            elif tx_type == "Income" and (to_acc == account_name or (from_acc == account_name and not to_acc)):
                inflow = amount
                running_bal += amount
                desc = f"รายรับ / เงินเดือนเข้า: {config.CATEGORIES.get(cat, {}).get('label', cat)}"
            elif tx_type == "Adjustment":
                if to_acc == account_name:
                    inflow = amount
                    running_bal += amount
                    desc = "ปรับยอดเงินเพิ่ม (+)"
                elif from_acc == account_name:
                    outflow = amount
                    running_bal -= amount
                    desc = "ปรับยอดเงินลด (-)"

            if inflow > 0 or outflow > 0:
                rows.append({
                    "Date": tx_date_str,
                    "Transaction_ID": tx_id,
                    "Type": tx_type,
                    "Description": desc,
                    "Inflow": inflow,
                    "Outflow": outflow,
                    "Balance": running_bal,
                    "Category": cat,
                    "Note": note
                })

        statement_df = pd.DataFrame(rows)
        # Sort descending for display
        return statement_df.iloc[::-1].reset_index(drop=True)

    # ------------------ MACROS ------------------

    def macro_weekly_allowance(self, target_date: date | None = None) -> dict:
        """
        Disburses weekly allowance: Thai Credit -> SCB (3,150 THB: 2,450 Food + 700 Transit).
        """
        d = target_date or date.today()
        return self.backend.add_transaction(
            date_val=d,
            tx_type="Internal_Transfer",
            from_account="Thai Credit",
            to_account="SCB",
            category="Other",
            amount=3150.0,
            note="⚡ จัดสรรงบสัปดาห์ (Weekly Allowance): อาหาร 2,450 + เดินทาง 700 THB"
        )

    def macro_transit_swipe(self, target_date: date | None = None, amount: float = 700.0) -> dict:
        """
        Credit card swipe for transit: SCB -> KBANK (700 THB) to maintain zero CC debt.
        """
        d = target_date or date.today()
        return self.backend.add_transaction(
            date_val=d,
            tx_type="Internal_Transfer",
            from_account="SCB",
            to_account="KBANK",
            category="Transit",
            amount=amount,
            note="🚆 แตะบัตรโดยสาร BTS/MRT สำรองเงินเข้า KBANK ทันที (Zero CC Debt)"
        )

    def macro_insurance_sinking(self, target_date: date | None = None) -> dict:
        """
        Monthly Insurance Sinking Fund: Thai Credit -> BAY (3,500 THB).
        """
        d = target_date or date.today()
        return self.backend.add_transaction(
            date_val=d,
            tx_type="Internal_Transfer",
            from_account="Thai Credit",
            to_account="BAY",
            category="Insurance_Fund",
            amount=3500.0,
            note="🛡️ โอนเงินสำรองประกันประจำงวด (Thai Credit -> BAY Insurance Fund)"
        )

    def macro_pay_credit_card_bill(self, amount: float | None = None, target_date: date | None = None) -> dict:
        """
        Credit Card Bill Payment Outflow: Deducts from KBANK (CC Reserve Buffer).
        """
        d = target_date or date.today()
        kbank_bal = self.get_accounts_summary()["kbank_balance"]
        pay_amount = amount if amount is not None and amount > 0 else kbank_bal
        if pay_amount <= 0:
            pay_amount = 0.0

        return self.backend.add_transaction(
            date_val=d,
            tx_type="Expense",
            from_account="KBANK",
            to_account=None,
            category="Credit_Card_Bill",
            amount=pay_amount,
            note="💳 ชำระยอดบิลบัตรเครดิต (ตัดจ่ายออกจากเงินพักสำรอง KBANK)"
        )

    def macro_salary_income(self, target_date: date | None = None, amount: float = 43000.0) -> dict:
        """
        Monthly Salary Inflow to Thai Credit HQ (43,000 THB) on 23rd.
        """
        d = target_date or date.today()
        return self.backend.add_transaction(
            date_val=d,
            tx_type="Income",
            from_account="",
            to_account="Thai Credit",
            category="Salary",
            amount=amount,
            note="💰 เงินเดือนเข้าบัญชีหลัก Thai Credit (Monthly Salary Inflow)"
        )
