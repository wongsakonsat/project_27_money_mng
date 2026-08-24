"""
Pytest suite for the Personal Finance Management System.
Covers cycle math, double-entry ledger reconciliation, and burn-rate pacing.

Run with:  pytest tests/
"""

import os
import sys
from datetime import date

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from cycle_utils import get_cycle_for_date, get_current_cycle_info, calculate_food_burn_metrics
from backend import FinanceBackend
from transaction_engine import TransactionEngine


@pytest.fixture
def engine(tmp_path):
    """A TransactionEngine backed by an isolated, throwaway SQLite file.
    No network calls, no shared state with the real app database."""
    db_path = str(tmp_path / "test_finance.db")
    backend = FinanceBackend(db_path=db_path, skip_remote_connect=True)
    backend.update_initial_balances({
        "Thai Credit": 10000.0,
        "SCB": 2000.0,
        "KBANK": 1500.0,
        "BAY": 40000.0,
    })
    return TransactionEngine(backend)


class TestCycleBoundaries:
    def test_cycle_starts_on_23rd(self):
        _, start, end, _ = get_cycle_for_date(date(2026, 8, 23))
        assert start == date(2026, 8, 23)
        assert end == date(2026, 9, 22)

    def test_cycle_just_before_23rd_belongs_to_previous_month(self):
        _, start, end, _ = get_cycle_for_date(date(2026, 8, 22))
        assert start == date(2026, 7, 23)
        assert end == date(2026, 8, 22)

    def test_cycle_wraps_across_year_boundary(self):
        _, start, end, _ = get_cycle_for_date(date(2027, 1, 1))
        assert start == date(2026, 12, 23)
        assert end == date(2027, 1, 22)


class TestDoubleEntryLedger:
    def test_initial_balances_seed_correctly(self, engine):
        summary = engine.get_accounts_summary()
        assert summary["thai_credit_balance"] == 10000.0
        assert summary["scb_balance"] == 2000.0
        assert summary["kbank_balance"] == 1500.0
        assert summary["bay_balance"] == 40000.0
        assert summary["total_net_worth"] == 53500.0

    def test_salary_income_credits_thai_credit(self, engine):
        engine.macro_salary_income(amount=43000.0)
        summary = engine.get_accounts_summary()
        assert summary["thai_credit_balance"] == 53000.0

    def test_weekly_allowance_transfers_thai_credit_to_scb(self, engine):
        engine.macro_salary_income(amount=43000.0)
        engine.macro_weekly_allowance()
        summary = engine.get_accounts_summary()
        assert summary["thai_credit_balance"] == 53000.0 - 3150.0
        assert summary["scb_balance"] == 2000.0 + 3150.0

    def test_expense_debits_source_account(self, engine):
        engine.backend.add_transaction(
            date_val=date.today(),
            tx_type="Expense",
            from_account="SCB",
            to_account=None,
            category="Food_Daily",
            amount=350.0,
            note="Lunch",
        )
        summary = engine.get_accounts_summary()
        assert summary["scb_balance"] == 2000.0 - 350.0

    def test_transit_swipe_moves_scb_to_kbank(self, engine):
        engine.macro_transit_swipe()
        summary = engine.get_accounts_summary()
        assert summary["scb_balance"] == 2000.0 - 700.0
        assert summary["kbank_balance"] == 1500.0 + 700.0

    def test_insurance_sinking_moves_thai_credit_to_bay(self, engine):
        engine.macro_insurance_sinking()
        summary = engine.get_accounts_summary()
        assert summary["thai_credit_balance"] == 10000.0 - 3500.0
        assert summary["bay_balance"] == 40000.0 + 3500.0

    def test_account_statement_records_every_transaction(self, engine):
        engine.macro_salary_income(amount=43000.0)
        engine.macro_weekly_allowance()
        engine.macro_transit_swipe()
        stmt_scb = engine.get_account_statement("SCB")
        assert not stmt_scb.empty
        assert len(stmt_scb) >= 2  # weekly allowance in + transit swipe out

    def test_deleting_a_transaction_reverts_its_balance_effect(self, engine):
        tx = engine.backend.add_transaction(
            date_val=date.today(),
            tx_type="Expense",
            from_account="SCB",
            to_account=None,
            category="Food_Daily",
            amount=350.0,
            note="Lunch",
        )
        assert engine.get_accounts_summary()["scb_balance"] == 2000.0 - 350.0

        engine.backend.delete_transaction(tx["Transaction_ID"])
        assert engine.get_accounts_summary()["scb_balance"] == 2000.0


class TestBurnRateMetrics:
    def test_remaining_budget_and_allowance_are_positive_when_under_budget(self):
        cycle_info = get_current_cycle_info()
        metrics = calculate_food_burn_metrics(spent_food=1050.0, cycle_info=cycle_info, base_daily_budget=350.0)
        assert metrics["spent_food"] == 1050.0
        assert metrics["remaining_budget"] > 0
        assert metrics["dynamic_daily_allowance"] > 0

    def test_overspending_flips_status_to_over_pace(self):
        cycle_info = get_current_cycle_info(as_of_date=date(2026, 8, 1))  # day 10 of the 23rd-22nd cycle
        metrics = calculate_food_burn_metrics(spent_food=100000.0, cycle_info=cycle_info, base_daily_budget=350.0)
        assert metrics["pace_diff"] > 350
        assert "Over Pace" in metrics["status_text"]


class TestPendingCreditCard:
    def test_add_and_get_pending_cc(self, engine):
        item = engine.backend.add_pending_cc(
            date_val=date(2026, 8, 24),
            item_name="Dinner with Team",
            category="Special_Meal",
            amount=600.0,
            note="Forgot to transfer"
        )
        assert item["Item_Name"] == "Dinner with Team"
        assert item["Amount"] == 600.0
        assert item["Status"] == "Pending"

        summary = engine.get_pending_cc_summary()
        assert summary["total_pending_amount"] == 600.0
        assert summary["pending_count"] == 1

    def test_clear_pending_cc_creates_transfer_to_kbank(self, engine):
        item = engine.backend.add_pending_cc(
            date_val=date(2026, 8, 24),
            item_name="Shopping Shoes",
            category="Wishlist_Hobby",
            amount=1500.0
        )
        init_scb = engine.get_accounts_summary()["scb_balance"]
        init_kbank = engine.get_accounts_summary()["kbank_balance"]

        # Clear from SCB -> KBANK
        tx = engine.backend.clear_pending_cc(item["Pending_ID"], from_account="SCB")
        assert tx is not None
        assert tx["Type"] == "Internal_Transfer"
        assert tx["From_Account"] == "SCB"
        assert tx["To_Account"] == "KBANK"
        assert tx["Amount"] == 1500.0

        summary = engine.get_accounts_summary()
        assert summary["scb_balance"] == init_scb - 1500.0
        assert summary["kbank_balance"] == init_kbank + 1500.0

        p_summary = engine.get_pending_cc_summary()
        assert p_summary["pending_count"] == 0
        assert p_summary["cleared_count"] == 1

    def test_delete_pending_cc(self, engine):
        item = engine.backend.add_pending_cc(
            date_val=date(2026, 8, 24),
            item_name="Mistake Entry",
            category="Other",
            amount=100.0
        )
        assert engine.get_pending_cc_summary()["pending_count"] == 1
        deleted = engine.backend.delete_pending_cc(item["Pending_ID"])
        assert deleted is True
        assert engine.get_pending_cc_summary()["pending_count"] == 0


class TestCreditCardsStatement:
    def test_get_credit_cards_seeds_defaults(self, engine):
        cards = engine.backend.get_credit_cards()
        assert len(cards) == 5
        card_names = [c["Card_Name"] for c in cards]
        assert "TTB Disney" in card_names
        assert "UOB One" in card_names
        assert "KBANK Credit Card" in card_names

    def test_pay_credit_card_records_expense_and_updates_card(self, engine):
        # Pay TTB Disney bill 27886.78 from KBANK
        init_kbank = engine.get_accounts_summary()["kbank_balance"]
        tx = engine.backend.pay_credit_card("ttb_disney", pay_amount=27886.78, from_account="KBANK")
        assert tx is not None
        assert tx["Type"] == "Expense"
        assert tx["From_Account"] == "KBANK"
        assert tx["Category"] == "Credit_Card_Bill"
        assert tx["Amount"] == 27886.78

        assert engine.get_accounts_summary()["kbank_balance"] == init_kbank - 27886.78
        cards = {c["Card_ID"]: c for c in engine.backend.get_credit_cards()}
        assert cards["ttb_disney"]["Status"] == "Paid"
        assert cards["ttb_disney"]["Remaining_Amount"] == 0.0

    def test_update_credit_card_statement_amount(self, engine):
        engine.backend.update_credit_card("scb_cardx", statement_amount=500.0)
        cards = {c["Card_ID"]: c for c in engine.backend.get_credit_cards()}
        assert cards["scb_cardx"]["Statement_Amount"] == 500.0
        assert cards["scb_cardx"]["Remaining_Amount"] == 500.0
        assert cards["scb_cardx"]["Status"] == "Unpaid"


class TestDailySummary:
    def test_get_today_summary(self, engine):
        today = date(2026, 8, 24)
        engine.backend.add_transaction(
            date_val=today,
            tx_type="Expense",
            from_account="SCB",
            to_account=None,
            category="Food_Daily",
            amount=150.0,
            note="Lunch"
        )
        summary = engine.get_today_summary(target_date=today)
        assert summary["today_expenses"] == 150.0
        assert summary["today_food"] == 150.0
        assert summary["food_remaining"] == 200.0
        assert summary["today_tx_count"] == 1



