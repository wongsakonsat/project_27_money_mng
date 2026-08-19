"""
SQLite Relational Database Manager
Provides ACID persistence, structured relational schemas, and fast queries for:
- Accounts & Running Balances
- Double-Entry Transactions
- Wishlist Goals
- App Settings & Google Sheets Sync Metadata
"""

import os
import sqlite3
import uuid
from datetime import datetime, date
import pandas as pd
import config
from cycle_utils import get_cycle_for_date

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "finance.db")

class FinanceDatabase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        """Creates SQLite tables and initial seed data if not present."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Accounts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_name TEXT PRIMARY KEY,
                    initial_balance REAL NOT NULL DEFAULT 0.0,
                    current_balance REAL NOT NULL DEFAULT 0.0,
                    updated_at TEXT NOT NULL
                )
            """)

            # Transactions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    cycle TEXT NOT NULL,
                    type TEXT NOT NULL,
                    from_account TEXT,
                    to_account TEXT,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Wishlist Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wishlist (
                    item_name TEXT PRIMARY KEY,
                    target_price REAL NOT NULL,
                    target_month TEXT,
                    priority TEXT DEFAULT 'Medium',
                    status TEXT DEFAULT 'Pending',
                    current_saved REAL DEFAULT 0.0
                )
            """)

            # Settings / Sync Config Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Seed default accounts if empty
            cursor.execute("SELECT COUNT(*) FROM accounts")
            if cursor.fetchone()[0] == 0:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for name, meta in config.ACCOUNTS.items():
                    cursor.execute("""
                        INSERT INTO accounts (account_name, initial_balance, current_balance, updated_at)
                        VALUES (?, ?, ?, ?)
                    """, (name, meta["default_initial"], meta["default_initial"], now_str))

            # Seed default wishlist if empty
            cursor.execute("SELECT COUNT(*) FROM wishlist")
            if cursor.fetchone()[0] == 0:
                for item in config.DEFAULT_WISHLIST:
                    cursor.execute("""
                        INSERT INTO wishlist (item_name, target_price, target_month, priority, status, current_saved)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (item["Item_Name"], item["Target_Price"], item["Target_Month"], item["Priority"], item["Status"], item["Current_Saved"]))

            conn.commit()

    # ------------------ ACCOUNTS ------------------

    def get_accounts(self) -> list[dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT account_name, initial_balance, current_balance, updated_at FROM accounts")
            rows = cursor.fetchall()
            return [
                {
                    "Account_Name": r["account_name"],
                    "Initial_Balance": float(r["initial_balance"]),
                    "Current_Balance": float(r["current_balance"]),
                    "Updated_At": r["updated_at"]
                }
                for r in rows
            ]

    def update_initial_balances(self, initial_map: dict[str, float]):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for name, init_val in initial_map.items():
                cursor.execute("""
                    INSERT INTO accounts (account_name, initial_balance, current_balance, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(account_name) DO UPDATE SET
                        initial_balance = excluded.initial_balance,
                        updated_at = excluded.updated_at
                """, (name, float(init_val), float(init_val), now_str))
            conn.commit()
        self.recalculate_all_balances()

    def recalculate_all_balances(self):
        """Calculates current balance for every account using double-entry ledger."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Fetch all initial balances
            cursor.execute("SELECT account_name, initial_balance FROM accounts")
            balances = {r["account_name"]: float(r["initial_balance"]) for r in cursor.fetchall()}

            # Fetch all transactions ordered chronologically
            cursor.execute("SELECT type, from_account, to_account, amount FROM transactions ORDER BY date ASC, created_at ASC")
            for r in cursor.fetchall():
                tx_type = r["type"]
                from_acc = r["from_account"]
                to_acc = r["to_account"]
                amt = float(r["amount"])

                if tx_type == "Expense":
                    if from_acc in balances:
                        balances[from_acc] -= amt
                elif tx_type == "Internal_Transfer":
                    if from_acc in balances:
                        balances[from_acc] -= amt
                    if to_acc in balances:
                        balances[to_acc] += amt
                elif tx_type == "Income":
                    dest = to_acc or from_acc
                    if dest in balances:
                        balances[dest] += amt
                elif tx_type == "Adjustment":
                    if to_acc in balances:
                        balances[to_acc] += amt
                    elif from_acc in balances:
                        balances[from_acc] -= amt

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for acc_name, current_bal in balances.items():
                cursor.execute("""
                    UPDATE accounts
                    SET current_balance = ?, updated_at = ?
                    WHERE account_name = ?
                """, (current_bal, now_str, acc_name))
            conn.commit()

    # ------------------ TRANSACTIONS ------------------

    def get_transactions(self) -> list[dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT transaction_id, date, cycle, type, from_account, to_account, category, amount, note, created_at
                FROM transactions
                ORDER BY date DESC, created_at DESC
            """)
            rows = cursor.fetchall()
            return [
                {
                    "Transaction_ID": r["transaction_id"],
                    "Date": r["date"],
                    "Cycle": r["cycle"],
                    "Type": r["type"],
                    "From_Account": r["from_account"] or "",
                    "To_Account": r["to_account"] or "",
                    "Category": r["category"],
                    "Amount": float(r["amount"]),
                    "Note": r["note"] or ""
                }
                for r in rows
            ]

    def add_transaction(self, date_val: str | date, tx_type: str, from_account: str | None,
                        to_account: str | None, category: str, amount: float, note: str = "") -> dict:
        if isinstance(date_val, (datetime, date)):
            date_str = date_val.strftime("%Y-%m-%d")
        else:
            date_str = str(date_val)

        cycle_id, _, _, _ = get_cycle_for_date(date_str)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tx_id = f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (transaction_id, date, cycle, type, from_account, to_account, category, amount, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tx_id, date_str, cycle_id, tx_type, from_account, to_account, category, float(amount), note, now_str))
            conn.commit()

        self.recalculate_all_balances()
        return {
            "Transaction_ID": tx_id,
            "Date": date_str,
            "Cycle": cycle_id,
            "Type": tx_type,
            "From_Account": from_account or "",
            "To_Account": to_account or "",
            "Category": category,
            "Amount": float(amount),
            "Note": note
        }

    def delete_transaction(self, tx_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE transaction_id = ?", (tx_id,))
            deleted = cursor.rowcount > 0
            conn.commit()

        if deleted:
            self.recalculate_all_balances()
        return deleted

    # ------------------ WISHLIST ------------------

    def get_wishlist(self) -> list[dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_name, target_price, target_month, priority, status, current_saved FROM wishlist")
            rows = cursor.fetchall()
            return [
                {
                    "Item_Name": r["item_name"],
                    "Target_Price": float(r["target_price"]),
                    "Target_Month": r["target_month"] or "",
                    "Priority": r["priority"],
                    "Status": r["status"],
                    "Current_Saved": float(r["current_saved"])
                }
                for r in rows
            ]

    def save_wishlist(self, items: list[dict]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM wishlist")
            for item in items:
                cursor.execute("""
                    INSERT INTO wishlist (item_name, target_price, target_month, priority, status, current_saved)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (item["Item_Name"], float(item["Target_Price"]), item.get("Target_Month", ""),
                      item.get("Priority", "Medium"), item.get("Status", "Pending"), float(item.get("Current_Saved", 0.0))))
            conn.commit()

    # ------------------ SETTINGS ------------------

    def get_setting(self, key: str, default: str = "") -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))
            conn.commit()
