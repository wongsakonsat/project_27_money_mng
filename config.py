"""
Configuration constants for Personal Finance Management App
Project 27: Multi-account Double-entry System with 23rd-22nd Custom Cycle
"""

# Base Financial Cycle & Income
MONTHLY_NET_INCOME = 43000.0  # THB
CYCLE_START_DAY = 23
CYCLE_END_DAY = 22

# Accounts Definition
ACCOUNTS = {
    "Thai Credit": {
        "id": "Thai Credit",
        "name": "Thai Credit (HQ / Primary)",
        "role": "Receives salary on 23rd, pays fixed bills & immediate commitments, disburses weekly allowance",
        "type": "Primary",
        "icon": "🏛️",
        "logo": "tcb.jpeg",
        "color": "#1E3A8A", # Deep Blue
        "default_initial": 15000.0
    },
    "SCB": {
        "id": "SCB",
        "name": "SCB (Daily Spending Wallet)",
        "role": "Receives weekly allowance (3,150 THB/wk = 2,450 Food + 700 Transit)",
        "type": "Operational",
        "icon": "💜",
        "logo": "scb.jpg",
        "color": "#6D28D9", # Purple
        "default_initial": 3150.0
    },
    "KBANK": {
        "id": "KBANK",
        "name": "KBANK (Credit Card Reserve Buffer)",
        "role": "Holds exact cash transferred immediately after credit card usage for zero CC debt",
        "type": "Buffer",
        "icon": "💚",
        "logo": "kbank.png",
        "color": "#047857", # Emerald Green
        "default_initial": 2000.0
    },
    "BAY": {
        "id": "BAY",
        "name": "BAY (Wealth Vault & Sinking Funds)",
        "role": "Emergency savings, Insurance Sinking Fund (3,500/mo), swept surpluses",
        "type": "Vault",
        "icon": "💛",
        "logo": "bay.png",
        "color": "#B45309", # Amber/Gold
        "default_initial": 50000.0
    }
}

ACCOUNT_NAMES = list(ACCOUNTS.keys())

# Budget Envelopes & Rules
BUDGET_RULES = {
    "Fixed Commitments (23rd Salary Day)": {
        "Mom": {"amount": 5000.0, "from_account": "Thai Credit", "category": "Mom", "type": "Expense", "note": "Family support"},
        "DCA Investment": {"amount": 4800.0, "from_account": "Thai Credit", "category": "DCA", "type": "Expense", "note": "Monthly DCA investment"},
        "Insurance Sinking Fund": {"amount": 3500.0, "from_account": "Thai Credit", "to_account": "BAY", "category": "Insurance_Fund", "type": "Internal_Transfer", "note": "Thai Credit -> BAY Insurance Fund"},
        "Rent Provision": {"amount": 6000.0, "from_account": "Thai Credit", "category": "Rent", "type": "Expense", "note": "Due at month-end, held in Thai Credit"},
        "Utilities & Phone": {"amount": 2650.0, "from_account": "Thai Credit", "category": "Utilities_Phone", "type": "Expense", "note": "Due ~15th, held in Thai Credit"}
    },
    "Daily Living (SCB Weekly Disbursed)": {
        "Weekly Allowance Total": 3150.0,
        "Daily Food Baseline": 350.0,  # THB/day (~10,500/month)
        "Transit Baseline": 700.0,     # THB/week (~2,800/month) -> Transferred to KBANK on card swipe
        "Special Meals Max Count": 2,  # up to 2 times/month
        "Special Meal Quota": 600.0    # 600 THB each (Total 1,200 THB)
    }
}

# Transaction Types
TRANSACTION_TYPES = [
    "Expense",           # โอนจ่ายภายนอก
    "Internal_Transfer", # โอนย้ายภายใน
    "Income",            # รายรับ
    "Adjustment"         # ปรับปรุงยอด / เงินเริ่มต้น
]

# Transaction Categories with friendly labels and icons
CATEGORIES = {
    "Food_Daily": {"label": "🍚 อาหารประจำวัน (Daily Food)", "icon": "🍚", "budget_group": "Daily Living"},
    "Special_Meal": {"label": "🍣 มื้อพิเศษ (Special Meal)", "icon": "🍣", "budget_group": "Daily Living"},
    "Transit": {"label": "🚆 เดินทาง BTS/MRT (Transit)", "icon": "🚆", "budget_group": "Daily Living"},
    "Mom": {"label": "❤️ ให้คุณแม่ (Family/Mom)", "icon": "❤️", "budget_group": "Fixed Commitments"},
    "Rent": {"label": "🏠 ค่าเช่าห้อง (Rent)", "icon": "🏠", "budget_group": "Fixed Commitments"},
    "Utilities_Phone": {"label": "⚡ ค่าน้ำ/ไฟ/เน็ต/โทรศัพท์ (Utilities)", "icon": "⚡", "budget_group": "Fixed Commitments"},
    "Insurance_Fund": {"label": "🛡️ เงินสำรองประกัน (Insurance Sinking)", "icon": "🛡️", "budget_group": "Sinking Funds"},
    "DCA": {"label": "📈 ลงทุน DCA (Investment)", "icon": "📈", "budget_group": "Investments"},
    "Wishlist_Hobby": {"label": "🎁 ช้อปปิ้ง / รางวัลชีวิต (Wishlist & Hobby)", "icon": "🎁", "budget_group": "Lifestyle"},
    "Credit_Card_Bill": {"label": "💳 ชำระบิลบัตรเครดิต (Credit Card Bill)", "icon": "💳", "budget_group": "Bills"},
    "Friend_Repay": {"label": "👥 เพื่อนโอนคืนค่าบัตร (Friend Repayment)", "icon": "👥", "budget_group": "Buffer"},
    "Salary": {"label": "💰 เงินเดือน (Salary Income)", "icon": "💰", "budget_group": "Income"},
    "Initial_Balance": {"label": "🏁 เงินตั้งต้นบัญชี (Initial Balance)", "icon": "🏁", "budget_group": "Setup"},
    "Other": {"label": "📦 อื่นๆ (Other)", "icon": "📦", "budget_group": "Other"}
}

CATEGORY_NAMES = list(CATEGORIES.keys())

# Default Wishlist Items
DEFAULT_WISHLIST = [
    {"Item_Name": "YSL Perfume", "Target_Price": 3500.0, "Target_Month": "2026-09", "Priority": "High", "Status": "In Progress", "Current_Saved": 1500.0},
    {"Item_Name": "Luca Bag", "Target_Price": 1400.0, "Target_Month": "2026-08", "Priority": "Medium", "Status": "In Progress", "Current_Saved": 1400.0},
    {"Item_Name": "White Sneakers", "Target_Price": 2800.0, "Target_Month": "2026-10", "Priority": "Medium", "Status": "Pending", "Current_Saved": 500.0},
    {"Item_Name": "Classic Watch", "Target_Price": 5500.0, "Target_Month": "2026-11", "Priority": "Low", "Status": "Pending", "Current_Saved": 1000.0},
]

# Credit Cards Statement Master & Due Dates
DEFAULT_CREDIT_CARDS = [
    {
        "card_id": "uob_one",
        "card_name": "UOB One",
        "bank_name": "UOB",
        "due_day": 18,
        "statement_amount": 359.71,
        "paid_amount": 360.00,
        "status": "Paid",
        "icon": "💳",
        "logo": "uob.png"
    },
    {
        "card_id": "ttb_disney",
        "card_name": "TTB Disney",
        "bank_name": "TTB",
        "due_day": 25,
        "statement_amount": 27886.78,
        "paid_amount": 0.0,
        "status": "Unpaid",
        "icon": "💳",
        "logo": "ttb.png"
    },
    {
        "card_id": "kbank_cc",
        "card_name": "KBANK Credit Card",
        "bank_name": "KBANK",
        "due_day": 5,
        "statement_amount": 58500.00,
        "paid_amount": 0.0,
        "status": "Unpaid",
        "icon": "💳",
        "logo": "kbank.png"
    },
    {
        "card_id": "scb_cardx",
        "card_name": "SCB CardX",
        "bank_name": "SCB",
        "due_day": 12,
        "statement_amount": 245.00,
        "paid_amount": 0.0,
        "status": "Unpaid",
        "icon": "💳",
        "logo": "scb.jpg"
    },
    {
        "card_id": "ktc_cc",
        "card_name": "KTC",
        "bank_name": "KTC",
        "due_day": 3,
        "statement_amount": 0.00,
        "paid_amount": 0.0,
        "status": "Paid",
        "icon": "💳",
        "logo": "ktc.png"
    },
]

