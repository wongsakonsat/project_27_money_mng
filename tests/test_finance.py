"""
Unit Tests for Personal Finance Management System
Tests cycle math, double-entry ledger reconciliation, and burn-rate pacing.
"""

import os
import sys
import shutil
from datetime import date

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from cycle_utils import get_cycle_for_date, get_current_cycle_info, calculate_food_burn_metrics
from backend import FinanceBackend
from transaction_engine import TransactionEngine

def test_cycle_boundaries():
    print("Testing cycle boundaries...")
    # Date on 23rd August -> cycle is 23 Aug to 22 Sep
    c_id, s_date, e_date, label = get_cycle_for_date(date(2026, 8, 23))
    assert s_date == date(2026, 8, 23), f"Expected 2026-08-23, got {s_date}"
    assert e_date == date(2026, 9, 22), f"Expected 2026-09-22, got {e_date}"

    # Date on 22nd August -> cycle is 23 Jul to 22 Aug
    c_id2, s_date2, e_date2, label2 = get_cycle_for_date(date(2026, 8, 22))
    assert s_date2 == date(2026, 7, 23), f"Expected 2026-07-23, got {s_date2}"
    assert e_date2 == date(2026, 8, 22), f"Expected 2026-08-22, got {e_date2}"

    # Date on 1st January -> cycle is 23 Dec (prev year) to 22 Jan
    c_id3, s_date3, e_date3, label3 = get_cycle_for_date(date(2027, 1, 1))
    assert s_date3 == date(2026, 12, 23), f"Expected 2026-12-23, got {s_date3}"
    assert e_date3 == date(2027, 1, 22), f"Expected 2027-01-22, got {e_date3}"
    print("✅ Cycle boundary tests passed!")

def test_double_entry_and_balances():
    print("Testing double-entry engine and initial balances...")
    test_db_path = os.path.join(os.path.dirname(__file__), "test_finance.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    from database import FinanceDatabase
    test_db = FinanceDatabase(db_path=test_db_path)
    
    # Custom test backend with isolated DB
    backend = FinanceBackend()
    backend.db = test_db
    engine = TransactionEngine(backend)

    # Set custom initial leftover balances
    custom_inits = {
        "Thai Credit": 10000.0,
        "SCB": 2000.0,
        "KBANK": 1500.0,
        "BAY": 40000.0
    }
    backend.update_initial_balances(custom_inits)
    
    summary0 = engine.get_accounts_summary()
    assert summary0["thai_credit_balance"] == 10000.0
    assert summary0["scb_balance"] == 2000.0
    assert summary0["kbank_balance"] == 1500.0
    assert summary0["bay_balance"] == 40000.0
    assert summary0["total_net_worth"] == 53500.0

    # 1. Macro Salary Inflow: +43,000 to Thai Credit
    tx_salary = engine.macro_salary_income(amount=43000.0)
    summary1 = engine.get_accounts_summary()
    assert summary1["thai_credit_balance"] == 53000.0

    # 2. Macro Weekly Allowance: Thai Credit -> SCB 3,150
    tx_weekly = engine.macro_weekly_allowance()
    summary2 = engine.get_accounts_summary()
    assert summary2["thai_credit_balance"] == 53000.0 - 3150.0 # 49850.0
    assert summary2["scb_balance"] == 2000.0 + 3150.0 # 5150.0

    # 3. Food Expense from SCB: 350
    tx_food = backend.add_transaction(
        date_val=date.today(),
        tx_type="Expense",
        from_account="SCB",
        to_account=None,
        category="Food_Daily",
        amount=350.0,
        note="Lunch"
    )
    summary3 = engine.get_accounts_summary()
    assert summary3["scb_balance"] == 5150.0 - 350.0 # 4800.0

    # 4. Transit Swipe: SCB -> KBANK 700
    tx_transit = engine.macro_transit_swipe()
    summary4 = engine.get_accounts_summary()
    assert summary4["scb_balance"] == 4800.0 - 700.0 # 4100.0
    assert summary4["kbank_balance"] == 1500.0 + 700.0 # 2200.0

    # 5. Insurance Sinking Transfer: Thai Credit -> BAY 3,500
    tx_ins = engine.macro_insurance_sinking()
    summary5 = engine.get_accounts_summary()
    assert summary5["thai_credit_balance"] == 49850.0 - 3500.0 # 46350.0
    assert summary5["bay_balance"] == 40000.0 + 3500.0 # 43500.0

    # Verify statement generation
    stmt_scb = engine.get_account_statement("SCB")
    assert not stmt_scb.empty
    assert len(stmt_scb) >= 3

    print("✅ Double-entry transactions and statements tests passed!")

def test_burn_rate_metrics():
    print("Testing dynamic food burn rate metrics...")
    cycle_info = get_current_cycle_info()
    metrics = calculate_food_burn_metrics(spent_food=1050.0, cycle_info=cycle_info, base_daily_budget=350.0)
    assert metrics["spent_food"] == 1050.0
    assert metrics["remaining_budget"] > 0
    assert metrics["dynamic_daily_allowance"] > 0
    print("✅ Burn rate metrics passed!")

if __name__ == "__main__":
    test_cycle_boundaries()
    test_double_entry_and_balances()
    test_burn_rate_metrics()
    print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
