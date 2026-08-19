"""
Data Backend Manager
Seamlessly connects SQLite Database (ACID local storage) with Google Sheets
via either Google Apps Script Webhook (Zero GCP config) or gspread Service Account.
"""

import os
import json
import uuid
import requests
from datetime import datetime, date
import pandas as pd
import config
from cycle_utils import get_cycle_for_date
from database import FinanceDatabase

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "service_account.json")

class FinanceBackend:
    def __init__(self):
        self.db = FinanceDatabase()
        self.gspread_client = None
        self.sheet = None
        self.is_connected_to_sheets = False
        self.connection_error = None
        self.sheet_title = "Money_Management_2026"
        self.webhook_url = self.db.get_setting("webhook_url", "")
        
        # Check webhook or service account
        if self.webhook_url:
            self.test_webhook_connection(self.webhook_url)
        elif os.path.exists(CREDENTIALS_FILE):
            self.connect_google_sheets()

    # ------------------ GOOGLE APPS SCRIPT WEBHOOK SYNC ------------------

    def set_webhook_url(self, url: str) -> bool:
        """Stores Webhook URL and tests connectivity."""
        url = url.strip()
        self.webhook_url = url
        self.db.set_setting("webhook_url", url)
        return self.test_webhook_connection(url)

    def test_webhook_connection(self, url: str) -> bool:
        if not url or not url.startswith("https://"):
            self.is_connected_to_sheets = False
            self.connection_error = "URL ต้องขึ้นต้นด้วย https://script.google.com/..."
            return False
        try:
            resp = requests.get(url, timeout=10, allow_redirects=True)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    self.is_connected_to_sheets = True
                    self.connection_error = None
                    return True
            self.is_connected_to_sheets = False
            self.connection_error = f"HTTP {resp.status_code}: {resp.text[:100]}"
            return False
        except Exception as e:
            self.is_connected_to_sheets = False
            self.connection_error = str(e)
            return False

    def sync_pull_from_webhook(self) -> bool:
        """Pulls latest records from Google Sheets via Webhook and updates SQLite DB."""
        if not self.webhook_url:
            return False
        try:
            resp = requests.get(self.webhook_url, timeout=15, allow_redirects=True)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    # Update Accounts
                    g_accounts = data.get("accounts", [])
                    if g_accounts:
                        inits = {}
                        for a in g_accounts:
                            name = a.get("Account_Name")
                            if name in config.ACCOUNT_NAMES and "Initial_Balance" in a:
                                try:
                                    inits[name] = float(a["Initial_Balance"])
                                except:
                                    pass
                        if inits:
                            self.db.update_initial_balances(inits)

                    # Update Wishlist
                    g_wishlist = data.get("wishlist", [])
                    if g_wishlist:
                        self.db.save_wishlist(g_wishlist)

                    return True
            return False
        except Exception as e:
            print(f"Error pulling from webhook: {e}")
            return False

    def sync_push_to_webhook(self) -> bool:
        """Pushes entire SQLite DB state to Google Sheets via Webhook."""
        if not self.webhook_url:
            return False
        try:
            payload = {
                "action": "sync_all",
                "accounts": self.db.get_accounts(),
                "transactions": self.db.get_transactions(),
                "wishlist": self.db.get_wishlist()
            }
            resp = requests.post(self.webhook_url, json=payload, timeout=15, allow_redirects=True)
            return resp.status_code == 200 and resp.json().get("status") == "success"
        except Exception as e:
            print(f"Error pushing to webhook: {e}")
            return False

    # ------------------ GSPREAD SERVICE ACCOUNT ------------------

    def connect_google_sheets(self, creds_path: str | None = None, sheet_identifier: str | None = None) -> bool:
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            target_creds = creds_path or CREDENTIALS_FILE
            if not os.path.exists(target_creds):
                self.is_connected_to_sheets = False
                self.connection_error = f"Credentials file '{os.path.basename(target_creds)}' not found."
                return False

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_file(target_creds, scopes=scopes)
            client = gspread.authorize(creds)
            self.gspread_client = client

            target_sheet = sheet_identifier or self.sheet_title
            if target_sheet.startswith("https://"):
                self.sheet = client.open_by_url(target_sheet)
            elif len(target_sheet) == 44 and "/" not in target_sheet and " " not in target_sheet:
                try:
                    self.sheet = client.open_by_key(target_sheet)
                except:
                    self.sheet = client.open(target_sheet)
            else:
                try:
                    self.sheet = client.open(target_sheet)
                except gspread.exceptions.SpreadsheetNotFound:
                    self.sheet = client.create(target_sheet)

            self.is_connected_to_sheets = True
            self.connection_error = None
            return True
        except Exception as e:
            self.is_connected_to_sheets = False
            self.connection_error = str(e)
            return False

    # ------------------ PASS-THROUGHS TO SQLITE DB ------------------

    def get_accounts(self) -> list[dict]:
        return self.db.get_accounts()

    def update_initial_balances(self, new_initial_balances: dict[str, float]):
        self.db.update_initial_balances(new_initial_balances)
        if self.is_connected_to_sheets:
            if self.webhook_url:
                self.sync_push_to_webhook()

    def recalculate_all_balances(self):
        self.db.recalculate_all_balances()

    def get_transactions(self) -> list[dict]:
        return self.db.get_transactions()

    def add_transaction(self, date_val: str | date, tx_type: str, from_account: str | None,
                        to_account: str | None, category: str, amount: float, note: str = "") -> dict:
        new_tx = self.db.add_transaction(
            date_val=date_val,
            tx_type=tx_type,
            from_account=from_account,
            to_account=to_account,
            category=category,
            amount=amount,
            note=note
        )
        # Push to webhook if connected
        if self.is_connected_to_sheets and self.webhook_url:
            try:
                requests.post(self.webhook_url, json={"action": "add_transaction", "transaction": new_tx}, timeout=5)
            except Exception as e:
                print(f"Non-blocking webhook push error: {e}")

        return new_tx

    def delete_transaction(self, tx_id: str) -> bool:
        deleted = self.db.delete_transaction(tx_id)
        if deleted and self.is_connected_to_sheets and self.webhook_url:
            self.sync_push_to_webhook()
        return deleted

    def get_wishlist(self) -> list[dict]:
        return self.db.get_wishlist()

    def save_wishlist(self, items: list[dict]):
        self.db.save_wishlist(items)
        if self.is_connected_to_sheets and self.webhook_url:
            self.sync_push_to_webhook()
