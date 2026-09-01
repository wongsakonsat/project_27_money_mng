"""
UI Components & Custom Styling Module (Clean Minimalist White Theme)
Clean, modern, high-contrast visual design with subtle accent indicators.
"""

import base64
import os
from datetime import date, datetime, timedelta
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import config

_LOGO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo")
_LOGO_MIME_BY_EXT = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}

_KNOWN_LOGOS = {
    "Thai Credit": "tcb.jpeg",
    "TCB": "tcb.jpeg",
    "tcb": "tcb.jpeg",
    "SCB": "scb.jpg",
    "scb": "scb.jpg",
    "scb_cardx": "scb.jpg",
    "SCB CardX": "scb.jpg",
    "KBANK": "kbank.png",
    "kbank": "kbank.png",
    "kbank_cc": "kbank.png",
    "KBANK Credit Card": "kbank.png",
    "BAY": "bay.png",
    "bay": "bay.png",
    "UOB": "uob.png",
    "uob": "uob.png",
    "uob_one": "uob.png",
    "UOB One": "uob.png",
    "TTB": "ttb.png",
    "ttb": "ttb.png",
    "ttb_disney": "ttb.png",
    "TTB Disney": "ttb.png",
    "KTC": "ktc.png",
    "ktc": "ktc.png",
    "ktc_cc": "ktc.png"
}

@st.cache_data
def get_bank_logo_data_uri(identifier: str) -> str | None:
    """Returns a base64 data: URI for the account or credit card bank logo (logo/*.png|jpg|jpeg)."""
    if not identifier:
        return None
    filename = config.ACCOUNTS.get(identifier, {}).get("logo")
    if not filename:
        filename = _KNOWN_LOGOS.get(identifier) or _KNOWN_LOGOS.get(str(identifier).lower())
    if not filename:
        for ext in [".png", ".jpg", ".jpeg"]:
            candidate = os.path.join(_LOGO_DIR, f"{str(identifier).lower()}{ext}")
            if os.path.exists(candidate):
                filename = f"{str(identifier).lower()}{ext}"
                break
    if not filename:
        return None

    path = os.path.join(_LOGO_DIR, filename)
    if not os.path.exists(path):
        return None
    mime = _LOGO_MIME_BY_EXT.get(os.path.splitext(filename)[1].lower(), "image/png")
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"

def get_bank_logo_html(account_name: str, size: int = 22) -> str:
    """Returns HTML img element for bank/card logo, or fallback emoji icon."""
    uri = get_bank_logo_data_uri(account_name)
    if uri:
        return f'<img class="bank-logo" src="{uri}" alt="{account_name}" style="width:{size}px; height:{size}px; border-radius:6px; vertical-align:middle; object-fit:cover; box-shadow:0 1px 2px rgba(0,0,0,0.08);">'
    acc = config.ACCOUNTS.get(account_name, {})
    return acc.get("icon", "💳" if "card" in str(account_name).lower() else "🏦")



CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Prompt:wght@300;400;500;600;700&display=swap');

/* Global Font & Clean Light Theme */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', 'Prompt', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}

/* App Header & Hero Banner */
.hero-container {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.hero-title {
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.4px;
    color: #0F172A;
    margin-bottom: 4px;
}

.hero-subtitle {
    color: #64748B;
    font-size: 13.5px;
    font-weight: 400;
}

/* Minimalist Clean Metric Cards */
.metric-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
    height: 100%;
}
.metric-card:hover {
    border-color: #CBD5E1;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.metric-label {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748B;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.metric-value {
    font-size: 24px;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.4px;
}

.metric-sub {
    font-size: 12px;
    color: #059669;
    margin-top: 6px;
}

.metric-sub.danger {
    color: #DC2626;
}

.metric-sub.warning {
    color: #D97706;
}

.metric-sub.neutral {
    color: #64748B;
}

/* Account Cards */
.account-card {
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #E2E8F0;
    background-color: #FFFFFF;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    margin-bottom: 12px;
    transition: transform 0.15s ease;
}
.account-card:hover {
    transform: translateY(-1px);
}

.account-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}

.account-name {
    font-weight: 600;
    font-size: 13.5px;
    color: #1E293B;
    display: flex;
    align-items: center;
    gap: 7px;
}

.bank-logo {
    width: 22px;
    height: 22px;
    border-radius: 6px;
    object-fit: cover;
    flex-shrink: 0;
    box-shadow: 0 0 0 1px rgba(0,0,0,0.06);
}

.account-balance {
    font-size: 22px;
    font-weight: 700;
    color: #0F172A;
}

.account-role {
    font-size: 11px;
    color: #64748B;
    margin-top: 4px;
    line-height: 1.4;
}

/* Clean Button Styles */
div.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13.5px !important;
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    transition: all 0.15s ease !important;
}

div.stButton > button:hover {
    background-color: #F1F5F9 !important;
    border-color: #94A3B8 !important;
    color: #0F172A !important;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background-color: #F1F5F9;
    padding: 4px;
    border-radius: 10px;
    border: 1px solid #E2E8F0;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    padding: 6px 14px;
    color: #64748B;
    font-weight: 500;
    font-size: 13.5px;
}

.stTabs [aria-selected="true"] {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}

/* Badge Pills */
.badge-pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 16px;
    font-size: 11px;
    font-weight: 600;
}
.badge-primary { background: #EFF6FF; color: #2563EB; border: 1px solid #BFDBFE; }
.badge-purple { background: #FAF5FF; color: #7C3AED; border: 1px solid #E9D5FF; }
.badge-emerald { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
.badge-amber { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.badge-rose { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }

/* Progress bar customizations */
.stProgress > div > div > div > div {
    background: #2563EB !important;
    border-radius: 6px;
}

/* Form & Input adjustments for clean look */
.stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div {
    border-radius: 8px !important;
    border-color: #CBD5E1 !important;
}
</style>
"""

def inject_styles():
    """Injects CSS into Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def render_hero_header(cycle_info: dict, summary: dict):
    """Renders clean white hero header highlighting Active Liquidity (Thai Credit + SCB)."""
    total_net_worth = summary["total_net_worth"]
    active_liquidity = summary["active_liquidity"]

    st.markdown(f"""
    <div class="hero-container">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
            <div>
                <div class="hero-title">💼 Financial Cockpit & Money Management</div>
                <div class="hero-subtitle">
                    📅 <b>{cycle_info['display_label']}</b> • ดำเนินการมาแล้ว <b>{cycle_info['days_elapsed']}</b> / {cycle_info['total_days']} วัน (เหลืออีก {cycle_info['days_remaining']} วัน)
                </div>
            </div>
            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                <div style="text-align: right; background: #EFF6FF; padding: 8px 16px; border-radius: 10px; border: 1px solid #BFDBFE;">
                    <div style="font-size: 10.5px; color: #1D4ED8; text-transform: uppercase; font-weight: 700;">⚡ สภาพคล่องหมุนเวียนจริง (Thai Credit + SCB)</div>
                    <div style="font-size: 22px; font-weight: 800; color: #1E40AF;">฿{active_liquidity:,.2f}</div>
                </div>
                <div style="text-align: right; background: #F8FAFC; padding: 8px 16px; border-radius: 10px; border: 1px solid #E2E8F0;">
                    <div style="font-size: 10.5px; color: #64748B; text-transform: uppercase; font-weight: 600;">💎 รวม 4 บัญชี (Total Net Worth)</div>
                    <div style="font-size: 22px; font-weight: 800; color: #059669;">฿{total_net_worth:,.2f}</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_kpi_cards(summary: dict, cycle_analytics: dict):
    """Renders top 4 analytical KPI cards with subtle clean accents."""
    col1, col2, col3, col4 = st.columns(4)
    
    cycle_info = cycle_analytics["cycle_info"]
    food_metrics = cycle_analytics["food_metrics"]
    special_used = cycle_analytics["special_meals_count"]
    special_max = cycle_analytics["special_meal_max"]
    kbank_bal = summary["kbank_balance"]
    active_liquidity = summary["active_liquidity"]

    with col1:
        # Dynamic color indicator based on pace
        allowance_color = "#DC2626" if food_metrics["pace_diff"] > 350 else "#059669" if food_metrics["pace_diff"] < -350 else "#2563EB"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🍚 งบอาหารคงเหลือ / วัน (SCB)</div>
            <div class="metric-value" style="color: {allowance_color};">฿{food_metrics['dynamic_daily_allowance']:,.0f} <span style="font-size: 13px; color: #64748B; font-weight: 400;">/วัน</span></div>
            <div class="metric-sub neutral" style="margin-top: 4px;">{food_metrics['status_text']} (เหลือ ฿{food_metrics['remaining_budget']:,.0f})</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        meal_color = "#059669" if special_used <= special_max else "#DC2626"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🍣 มื้อพิเศษ Special Meals</div>
            <div class="metric-value" style="color: {meal_color};">{special_used} / {special_max} <span style="font-size: 13px; color: #64748B; font-weight: 400;">ครั้ง</span></div>
            <div class="metric-sub neutral" style="margin-top: 4px;">โควตา 600฿ x 2 (ใช้ไป ฿{cycle_analytics['special_meals_spent']:,.0f})</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💳 เงินพักรอจ่ายบัตร (KBANK)</div>
            <div class="metric-value" style="color: #059669;">฿{kbank_bal:,.2f}</div>
            <div class="metric-sub neutral" style="margin-top: 4px;">สำรองยอดรูดบัตร (รอตัดจ่ายออก)</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">⚡ สภาพคล่องหมุนเวียน (Thai Credit + SCB)</div>
            <div class="metric-value" style="color: #2563EB;">฿{active_liquidity:,.0f}</div>
            <div class="metric-sub neutral" style="margin-top: 4px;">เงินดำเนินชีวิตหลัก (ไม่รวมเงินเก็บ/รอตัดบัตร)</div>
        </div>
        """, unsafe_allow_html=True)

def render_account_cards(accounts_dict: dict):
    """Renders clean white cards for all 4 bank accounts with subtle top accents and role tags."""
    cols = st.columns(4)
    # Accent color and badge mapping
    meta_map = {
        "Thai Credit": {"color": "#2563EB", "tag": "⚡ เงินหมุนเวียนหลัก (HQ)", "bg": "#EFF6FF", "tc": "#1D4ED8"},
        "SCB": {"color": "#7C3AED", "tag": "⚡ กระเป๋าใช้จ่าย (Wallet)", "bg": "#FAF5FF", "tc": "#6D28D9"},
        "KBANK": {"color": "#059669", "tag": "💳 พักเงินรอตัดบัตร (Buffer)", "bg": "#ECFDF5", "tc": "#047857"},
        "BAY": {"color": "#D97706", "tag": "🔒 เงินเก็บยาว (Vault)", "bg": "#FFFBEB", "tc": "#B45309"}
    }
    
    for i, (name, acc) in enumerate(accounts_dict.items()):
        with cols[i]:
            m = meta_map.get(name, {"color": "#2563EB", "tag": acc["type"], "bg": "#F1F5F9", "tc": "#475569"})
            logo_uri = get_bank_logo_data_uri(name)
            icon_html = f'<img class="bank-logo" src="{logo_uri}" alt="{name} logo">' if logo_uri else acc['icon']
            st.markdown(f"""
            <div class="account-card" style="border-top: 3px solid {m['color']};">
                <div class="account-header">
                    <span class="account-name">{icon_html} {acc['name']}</span>
                    <span class="badge-pill" style="background: {m['bg']}; color: {m['tc']}; font-size: 10px;">{m['tag']}</span>
                </div>
                <div class="account-balance">฿{acc['current_balance']:,.2f}</div>
                <div class="account-role">{acc['role']}</div>
                <div style="margin-top: 6px; font-size: 11px; color: #94A3B8;">เงินต้นเริ่มต้น: ฿{acc['initial_balance']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

def plot_daily_food_burn_chart(cycle_info: dict, food_metrics: dict, transactions: list[dict]):
    """Plots clean light ideal vs actual daily food burn curve."""
    total_days = cycle_info["total_days"]
    base_daily = food_metrics["base_daily_budget"]
    start_date = cycle_info["start_date"]
    
    dates = [start_date + pd.Timedelta(days=i) for i in range(total_days)]
    ideal_cumulative = [(i + 1) * base_daily for i in range(total_days)]
    
    df = pd.DataFrame(transactions)
    daily_gross = {d: 0.0 for d in dates}
    daily_repay = {d: 0.0 for d in dates}
    if not df.empty and "Category" in df.columns:
        for _, r in df.iterrows():
            try:
                d_raw = r.get("Date")
                d_obj = datetime.strptime(str(d_raw)[:10], "%Y-%m-%d").date() if isinstance(d_raw, str) else (d_raw if isinstance(d_raw, date) else d_raw.date())
                if d_obj in daily_gross:
                    tx_type = r.get("Type")
                    cat = r.get("Category")
                    amt = float(r.get("Amount", 0.0))
                    to_acc = r.get("To_Account")
                    if tx_type == "Expense" and cat == "Food_Daily":
                        daily_gross[d_obj] += amt
                    elif tx_type == "Internal_Transfer" and to_acc == "KBANK" and cat == "Food_Daily":
                        daily_gross[d_obj] += amt
                    elif tx_type == "Income" and cat == "Friend_Repay":
                        note = str(r.get("Note", "")).lower()
                        if "คอนโด" not in note and "rent" not in note and "ค่าเช่า" not in note:
                            daily_repay[d_obj] += amt
            except:
                pass
    
    actual_spent_by_date = {d: max(0.0, daily_gross[d] - daily_repay[d]) for d in dates}
    
    actual_cumulative = []
    running = 0.0
    today_date = cycle_info["as_of_date"]
    
    for d in dates:
        if d <= today_date:
            running += actual_spent_by_date.get(d, 0.0)
            actual_cumulative.append(running)
        else:
            actual_cumulative.append(None)
            
    fig = go.Figure()
    
    # Ideal plan line
    fig.add_trace(go.Scatter(
        x=[d.strftime("%d %b") for d in dates],
        y=ideal_cumulative,
        mode="lines",
        name="งบตามแผน (฿350/วัน)",
        line=dict(color="#94A3B8", width=2, dash="dash"),
        hovertemplate="งบตามแผน: ฿%{y:,.2f}<extra></extra>"
    ))
    
    # Actual spend line
    fig.add_trace(go.Scatter(
        x=[d.strftime("%d %b") for d in dates],
        y=actual_cumulative,
        mode="lines+markers",
        name="จ่ายจริงสะสม (Food)",
        line=dict(color="#DC2626" if food_metrics.get("pace_diff", 0) > 350 else "#059669", width=2.8),
        marker=dict(size=6, symbol="circle"),
        hovertemplate="จ่ายจริงสะสม: ฿%{y:,.2f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="📈 การใช้จ่ายงบอาหารเทียบกับแผน (Food Burn Rate Pacing)",
            font=dict(color="#0F172A", size=13.5, family="Prompt, Inter", weight="bold"),
            x=0, y=0.98
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#334155", family="Prompt, Inter", size=12),
        margin=dict(l=35, r=20, t=65, b=35),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font_size=12,
            font_family="Prompt, Inter",
            bordercolor="#CBD5E1"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#475569")
        ),
        xaxis=dict(
            gridcolor="#F8FAFC",
            linecolor="#E2E8F0",
            nticks=8,
            tickangle=0,
            tickfont=dict(size=11, color="#64748B")
        ),
        yaxis=dict(
            gridcolor="#F1F5F9",
            linecolor="#E2E8F0",
            title=dict(text="บาท (THB)", font=dict(size=11, color="#64748B")),
            tickfont=dict(size=11, color="#64748B")
        ),
        height=350
    )
    return fig

def plot_monthly_expense_surplus_tracker(cycle_info: dict, cycle_plan: dict, transactions: list[dict], cycle_analytics: dict):
    """
    Plots the monthly total expense burn-up vs planned expense ceiling,
    tracking whether the user will reach their target end-of-month surplus.
    """
    start_val = cycle_info.get("start_date")
    try:
        if isinstance(start_val, (datetime, date)):
            start_d = start_val if isinstance(start_val, date) else start_val.date()
        else:
            start_d = datetime.strptime(str(start_val)[:10], "%Y-%m-%d").date()
    except Exception:
        start_d = date.today()

    end_val = cycle_info.get("end_date")
    try:
        if isinstance(end_val, (datetime, date)):
            end_d = end_val if isinstance(end_val, date) else end_val.date()
        else:
            end_d = datetime.strptime(str(end_val)[:10], "%Y-%m-%d").date()
    except Exception:
        end_d = start_d + timedelta(days=30)

    as_of_val = cycle_info.get("as_of_date")
    try:
        if isinstance(as_of_val, (datetime, date)):
            today_d = as_of_val if isinstance(as_of_val, date) else as_of_val.date()
        elif isinstance(as_of_val, str) and len(as_of_val) >= 10 and as_of_val[:4].isdigit():
            today_d = datetime.strptime(as_of_val[:10], "%Y-%m-%d").date()
        else:
            today_d = date.today()
    except Exception:
        today_d = date.today()
    
    total_days = cycle_info.get("total_days", max(1, (end_d - start_d).days + 1))
    days_elapsed = cycle_info.get("days_elapsed", max(1, (today_d - start_d).days + 1))
    days_remaining = cycle_info.get("days_remaining", max(0, (end_d - today_d).days))
    
    planned_income = float(cycle_plan.get("planned_income", 45000.0))
    target_surplus = float(cycle_plan.get("target_surplus", 1516.90))
    planned_expense = max(0.0, planned_income - target_surplus)
    
    # Generate list of dates
    num_days = max(1, (end_d - start_d).days + 1)
    dates = [start_d + timedelta(days=i) for i in range(num_days)]
    
    # Group actual expenses and commitments by date in this cycle
    daily_gross_all = {d: 0.0 for d in dates}
    daily_repay_all = {d: 0.0 for d in dates}
    if transactions:
        tx_df = pd.DataFrame(transactions)
        if not tx_df.empty and "Category" in tx_df.columns:
            for _, r in tx_df.iterrows():
                try:
                    d_raw = r.get("Date")
                    d_obj = datetime.strptime(str(d_raw)[:10], "%Y-%m-%d").date() if isinstance(d_raw, str) else (d_raw if isinstance(d_raw, date) else d_raw.date())
                    if d_obj in daily_gross_all:
                        tx_type = r.get("Type")
                        cat = r.get("Category")
                        amt = float(r.get("Amount", 0.0))
                        to_acc = r.get("To_Account")
                        from_acc = r.get("From_Account")
                        
                        if tx_type == "Expense":
                            daily_gross_all[d_obj] += amt
                        elif tx_type == "Internal_Transfer":
                            if to_acc == "KBANK" and cat in ["Food_Daily", "Special_Meal", "Transit", "Wishlist_Hobby", "Mom", "Utilities_Phone", "Other"]:
                                daily_gross_all[d_obj] += amt
                            elif from_acc == "Thai Credit" and cat in ["Utilities_Phone", "Mom", "Rent", "DCA"]:
                                daily_gross_all[d_obj] += amt
                        elif tx_type == "Income" and cat == "Friend_Repay":
                            note = str(r.get("Note", "")).lower()
                            if "คอนโด" not in note and "rent" not in note and "ค่าเช่า" not in note:
                                daily_repay_all[d_obj] += amt
                except:
                    pass
                    
    actual_spent_by_date = {d: max(0.0, daily_gross_all[d] - daily_repay_all[d]) for d in dates}
                    
    # Build planned curve (linear pacing) vs actual cumulative
    planned_cumulative = []
    actual_cumulative = []
    running_actual = 0.0
    
    for idx, d in enumerate(dates):
        # Planned linear trajectory
        p_val = ((idx + 1) / len(dates)) * planned_expense
        planned_cumulative.append(p_val)
        
        if d <= today_d:
            running_actual += actual_spent_by_date.get(d, 0.0)
            actual_cumulative.append(running_actual)
        else:
            actual_cumulative.append(None)
            
    current_actual_total = running_actual
    expected_pace_today = (days_elapsed / total_days) * planned_expense if total_days > 0 else 0.0
    pace_diff = current_actual_total - expected_pace_today
    
    # Smart projection of remaining spend in cycle:
    daily_living_rate = float(config.BUDGET_RULES["Daily Living (SCB Weekly Disbursed)"]["Daily Food Baseline"]) + (float(config.BUDGET_RULES["Daily Living (SCB Weekly Disbursed)"]["Transit Baseline"]) / 7.0)
    remaining_living_projected = max(0, days_remaining) * daily_living_rate
    
    # Remaining unpaid fixed commitments in cycle
    fixed_status = cycle_analytics.get("fixed_status", {})
    remaining_fixed = 0.0
    for k, v in fixed_status.items():
        if not v.get("done", False):
            remaining_fixed += max(0.0, float(v.get("budget", 0.0)) - float(v.get("spent", 0.0)))
            
    ins_status = cycle_analytics.get("insurance_status", {})
    if not ins_status.get("done", False):
        remaining_fixed += max(0.0, float(ins_status.get("budget", 3500.0)) - float(ins_status.get("funded", 0.0)))
        
    projected_total_expense = current_actual_total + remaining_living_projected + remaining_fixed
    projected_surplus = planned_income - projected_total_expense

    fig = go.Figure()
    
    # Planned Expense Ceiling Trajectory
    fig.add_trace(go.Scatter(
        x=[d.strftime("%d %b") for d in dates],
        y=planned_cumulative,
        mode="lines",
        name=f"เพดานงบตามแผน (เป้าเหลือ ฿{target_surplus:,.0f})",
        line=dict(color="#64748B", width=2, dash="dash"),
        hovertemplate="เพดานงบตามแผน: ฿%{y:,.2f}<extra></extra>"
    ))
    
    # Actual Total Outflow
    line_color = "#DC2626" if pace_diff > (planned_expense * 0.1) else "#2563EB"
    fig.add_trace(go.Scatter(
        x=[d.strftime("%d %b") for d in dates],
        y=actual_cumulative,
        mode="lines+markers",
        name="จ่ายสะสมจริง (Actual Outflow)",
        line=dict(color=line_color, width=2.8),
        marker=dict(size=6, color=line_color),
        fill="tozeroy",
        fillcolor="rgba(37, 99, 235, 0.05)",
        hovertemplate="จ่ายสะสมจริง: ฿%{y:,.2f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="📊 แทรคภาพรวมค่าใช้จ่าย & การคุมเป้าหมายเงินเหลือประจำงวด",
            font=dict(color="#0F172A", size=13.5, family="Prompt, Inter", weight="bold"),
            x=0, y=0.98
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#334155", family="Prompt, Inter", size=12),
        margin=dict(l=35, r=20, t=65, b=35),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font_size=12,
            font_family="Prompt, Inter",
            bordercolor="#CBD5E1"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#475569")
        ),
        xaxis=dict(
            gridcolor="#F8FAFC",
            linecolor="#E2E8F0",
            nticks=8,
            tickangle=0,
            tickfont=dict(size=11, color="#64748B")
        ),
        yaxis=dict(
            gridcolor="#F1F5F9",
            linecolor="#E2E8F0",
            title=dict(text="ยอดใช้จ่ายสะสม (THB)", font=dict(size=11, color="#64748B")),
            tickfont=dict(size=11, color="#64748B")
        ),
        height=350
    )
    
    return {
        "fig": fig,
        "planned_income": planned_income,
        "target_surplus": target_surplus,
        "planned_expense": planned_expense,
        "current_actual_total": current_actual_total,
        "expected_pace_today": expected_pace_today,
        "pace_diff": pace_diff,
        "projected_surplus": projected_surplus
    }

def plot_category_spend_donut(cat_spend: dict):
    """Plots clean donut chart of expenses by category."""
    data = []
    for cat, amt in cat_spend.items():
        if amt > 0 and cat not in ["Salary", "Initial_Balance"]:
            meta = config.CATEGORIES.get(cat, {"label": cat, "icon": "📦"})
            data.append({"Category": meta["label"], "Amount": amt})
            
    if not data:
        fig = go.Figure()
        fig.update_layout(
            title="🍩 สัดส่วนรายจ่าย (ยังไม่มีรายการในรอบนี้)",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=dict(color="#94A3B8"),
            height=320
        )
        return fig
        
    df = pd.DataFrame(data)
    # Clean tasteful pastel / subtle palette
    clean_palette = ["#3B82F6", "#8B5CF6", "#10B981", "#F59E0B", "#EC4899", "#6366F1", "#14B8A6", "#64748B"]
    fig = px.pie(
        df,
        names="Category",
        values="Amount",
        hole=0.6,
        title="🍩 สัดส่วนรายจ่ายประจำรอบบิล",
        color_discrete_sequence=clean_palette
    )
    fig.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#334155", family="Prompt, Inter", size=12),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="v", yanchor="middle", y=0.5),
        height=320
    )
    return fig

def render_pending_cc_kpis(pending_summary: dict, accounts_summary: dict):
    """Renders top metric cards for Pending CC Backing Tab."""
    cols = st.columns(4)
    total_unbacked = pending_summary["total_pending_amount"]
    pending_count = pending_summary["pending_count"]
    scb_bal = accounts_summary["scb_balance"]
    tc_bal = accounts_summary["thai_credit_balance"]
    kbank_bal = accounts_summary["kbank_balance"]

    with cols[0]:
        val_color = "#DC2626" if total_unbacked > 0 else "#059669"
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid {val_color};">
            <div class="metric-label">🔴 ค่าบัตรรอโอนเข้า KBANK</div>
            <div class="metric-value" style="color: {val_color};">฿{total_unbacked:,.2f}</div>
            <div class="metric-sub {'danger' if total_unbacked > 0 else 'neutral'}">
                {'⚠️ ต้องหาเงินมาโอนเข้า KBANK' if total_unbacked > 0 else '✅ ไม่มีค่าบัตรค้างโอน (ครบสมบูรณ์)'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #7C3AED;">
            <div class="metric-label">⏳ รายการที่ยังค้าง</div>
            <div class="metric-value">{pending_count} <span style="font-size: 15px; color: #64748B;">รายการ</span></div>
            <div class="metric-sub neutral">เคลียร์แล้วทั้งหมด {pending_summary['cleared_count']} รายการ</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        logo_scb = get_bank_logo_html("SCB", 18)
        can_cover_scb = scb_bal >= total_unbacked and total_unbacked > 0
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #7C3AED;">
            <div class="metric-label">{logo_scb} ยอดพร้อมโอนใน SCB</div>
            <div class="metric-value">฿{scb_bal:,.2f}</div>
            <div class="metric-sub {'neutral' if can_cover_scb else 'warning'}">
                {'✅ พอเคลียร์ยอดค้างทั้งหมด' if can_cover_scb else 'เงินในกระเป๋า SCB ปัจจุบัน'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[3]:
        logo_kbank = get_bank_logo_html("KBANK", 18)
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #059669;">
            <div class="metric-label">{logo_kbank} ยอดสำรองใน KBANK</div>
            <div class="metric-value">฿{kbank_bal:,.2f}</div>
            <div class="metric-sub neutral">เงินสำรองพร้อมจ่ายบิลรอบนี้</div>
        </div>
        """, unsafe_allow_html=True)

def render_credit_card_kpis(cc_summary: dict):
    """Renders top metric cards for Credit Card Statements & Bills."""
    cols = st.columns(4)
    total_remaining = cc_summary["total_remaining"]
    total_statement = cc_summary["total_statement"]
    kbank_bal = cc_summary["kbank_balance"]
    buffer_diff = cc_summary["buffer_diff"]
    is_safe = cc_summary["is_safe"]

    with cols[0]:
        val_color = "#DC2626" if total_remaining > 0 else "#059669"
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid {val_color};">
            <div class="metric-label">💳 ยอดบิลบัตรเครดิตที่ต้องจ่าย</div>
            <div class="metric-value" style="color: {val_color};">฿{total_remaining:,.2f}</div>
            <div class="metric-sub neutral">ยอดรวมตามใบแจ้งยอด: ฿{total_statement:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        logo_kbank = get_bank_logo_html("KBANK", 18)
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #059669;">
            <div class="metric-label">{logo_kbank} ยอดเงินสำรองใน KBANK</div>
            <div class="metric-value" style="color: #059669;">฿{kbank_bal:,.2f}</div>
            <div class="metric-sub neutral">เงินสดที่เตรียมไว้ตัดจ่ายบิลบัตร</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        status_color = "#059669" if is_safe else "#DC2626"
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid {status_color};">
            <div class="metric-label">🛡️ สภาพคล่องสำรอง (Buffer Health)</div>
            <div class="metric-value" style="color: {status_color};">
                {'+฿' if buffer_diff >= 0 else '-฿'}{abs(buffer_diff):,.2f}
            </div>
            <div class="metric-sub {'neutral' if is_safe else 'danger'}">
                {'✅ เงินสำรองใน KBANK พอจ่ายครบ 100%' if is_safe else '⚠️ เงินใน KBANK ไม่พอจ่ายบิล'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[3]:
        unpaid = cc_summary["unpaid_count"]
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #2563EB;">
            <div class="metric-label">📋 บัตรที่รอตัดชำระ</div>
            <div class="metric-value">{unpaid} <span style="font-size: 15px; color: #64748B;">/ {len(cc_summary['cards'])} ใบ</span></div>
            <div class="metric-sub neutral">ชำระครบแล้ว {len(cc_summary['cards']) - unpaid} ใบ</div>
        </div>
        """, unsafe_allow_html=True)

def render_due_credit_card_alerts(cc_summary: dict, today_date: date | None = None):
    """Renders prominent warning banner on Dashboard if any credit card is due within <= 5 days."""
    today = today_date or date.today()
    cards = cc_summary.get("cards", [])
    
    due_soon_cards = []
    for card in cards:
        rem_amt = card["Remaining_Amount"]
        if rem_amt <= 0:
            continue
        due_d = card["Due_Day"]
        # Calculate target due date
        if today.day >= 23:
            if due_d >= 23:
                target = date(today.year, today.month, due_d)
            else:
                m = today.month + 1 if today.month < 12 else 1
                y = today.year if today.month < 12 else today.year + 1
                target = date(y, m, due_d)
        else:
            if due_d <= 22:
                target = date(today.year, today.month, due_d)
            else:
                m = today.month - 1 if today.month > 1 else 12
                y = today.year if today.month > 1 else today.year - 1
                target = date(y, m, due_d)
                
        days_left = (target - today).days
        if days_left <= 5:
            due_soon_cards.append({
                "card": card,
                "target_date": target,
                "days_left": days_left
            })

    if not due_soon_cards:
        return

    # Render alert banner
    for item in due_soon_cards:
        card = item["card"]
        days_left = item["days_left"]
        logo_html = get_bank_logo_html(card["Card_ID"], 22)
        rem_amt = card["Remaining_Amount"]
        
        if days_left == 0:
            badge_text = "🚨 ครบกำหนดชำระวันนี้!"
            bg_color = "#FEF2F2"
            border_color = "#DC2626"
            text_color = "#991B1B"
        elif days_left == 1:
            badge_text = "⚠️ ครบกำหนดชำระพรุ่งนี้!"
            bg_color = "#FEF2F2"
            border_color = "#DC2626"
            text_color = "#991B1B"
        elif days_left < 0:
            badge_text = f"🚨 เกินกำหนดชำระมาแล้ว {abs(days_left)} วัน!"
            bg_color = "#FEF2F2"
            border_color = "#DC2626"
            text_color = "#991B1B"
        else:
            badge_text = f"⏳ เหลือเวลาชำระอีก {days_left} วัน (วันที่ {card['Due_Day']})"
            bg_color = "#FFFBEB"
            border_color = "#F59E0B"
            text_color = "#92400E"

        st.markdown(f"""
        <div style="background-color: {bg_color}; border: 1.5px solid {border_color}; border-radius: 12px; padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    {logo_html}
                    <div>
                        <div style="font-weight: 700; font-size: 15px; color: {text_color};">
                            {card['Card_Name']} — <span style="font-size: 13px; font-weight: 600;">{badge_text}</span>
                        </div>
                        <div style="font-size: 12px; color: #64748B; margin-top: 2px;">
                            วันครบกำหนด: <b>{item['target_date'].strftime('%d %b %Y')}</b> • ยอดที่ต้องชำระ: <b style="color: #DC2626; font-size: 14px;">฿{rem_amt:,.2f}</b>
                        </div>
                    </div>
                </div>
                <div>
                    <span class="badge-pill badge-rose" style="font-size: 12px; padding: 4px 10px;">
                        ยอดค้าง: ฿{rem_amt:,.2f}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_today_expense_summary(today_summary: dict):
    """Renders daily expense summary with food pacing quota and today's total outflow."""
    cols = st.columns(3)
    today_food = today_summary["today_food"]
    food_base = today_summary["food_baseline"]
    food_rem = today_summary["food_remaining"]
    today_exp = today_summary["today_expenses"]
    today_tx_cnt = today_summary["today_tx_count"]
    today_date_str = today_summary["today_date_str"]

    with cols[0]:
        food_status_cls = "neutral" if food_rem >= 0 else "danger"
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #7C3AED;">
            <div class="metric-label">🍚 งบอาหารวันนี้ (Food Quota)</div>
            <div class="metric-value">฿{today_food:,.2f} <span style="font-size: 14px; color: #64748B;">/ ฿{food_base:,.0f}</span></div>
            <div class="metric-sub {food_status_cls}">
                {'✅ เหลือโควต้าอาหารวันนี้: ฿' + f'{food_rem:,.2f}' if food_rem >= 0 else '⚠️ ใช้อาหารเกินโควตาวันนี้: ฿' + f'{abs(food_rem):,.2f}'}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #2563EB;">
            <div class="metric-label">💸 รายจ่ายรวมวันนี้ ({today_date_str})</div>
            <div class="metric-value" style="color: #2563EB;">฿{today_exp:,.2f}</div>
            <div class="metric-sub neutral">บันทึกแล้วทั้งหมด {today_tx_cnt} รายการวันนี้</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        transit = today_summary["today_transit"]
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #059669;">
            <div class="metric-label">🚆 เดินทาง BTS/MRT วันนี้</div>
            <div class="metric-value">฿{transit:,.2f}</div>
            <div class="metric-sub neutral">โควต้าเดินทางประจำสัปดาห์: ฿1,000.00</div>
        </div>
        """, unsafe_allow_html=True)


def render_daily_food_pacing_table(cycle_info: dict, transactions: list):
    """
    Renders an elegant, detailed table of daily food burn rate,
    showing Gross spend, Friend repayments, Net personal spend, Daily Budget comparison,
    and cumulative pacing from Day 1 to Today.
    """
    start_date = cycle_info["start_date"]
    end_date = cycle_info["end_date"]
    today_date = cycle_info["as_of_date"]
    base_daily = 350.0
    
    total_days = max(1, (end_date - start_date).days + 1)
    dates = [start_date + pd.Timedelta(days=i) for i in range(total_days)]
    
    df = pd.DataFrame(transactions)
    daily_gross = {d.date() if isinstance(d, pd.Timestamp) else d: 0.0 for d in dates}
    daily_repay = {d.date() if isinstance(d, pd.Timestamp) else d: 0.0 for d in dates}
    daily_notes = {d.date() if isinstance(d, pd.Timestamp) else d: [] for d in dates}
    
    if not df.empty and "Category" in df.columns:
        for _, r in df.iterrows():
            try:
                d_raw = r.get("Date")
                d_obj = datetime.strptime(str(d_raw)[:10], "%Y-%m-%d").date() if isinstance(d_raw, str) else (d_raw if isinstance(d_raw, date) else d_raw.date())
                if d_obj in daily_gross:
                    tx_type = r.get("Type")
                    cat = r.get("Category")
                    amt = float(r.get("Amount", 0.0))
                    to_acc = r.get("To_Account")
                    note = str(r.get("Note", ""))
                    note_l = note.lower()
                    
                    if tx_type == "Expense" and cat == "Food_Daily":
                        daily_gross[d_obj] += amt
                        if note:
                            daily_notes[d_obj].append(f"{note} (฿{amt:,.0f})")
                    elif tx_type == "Internal_Transfer" and to_acc == "KBANK" and cat == "Food_Daily":
                        daily_gross[d_obj] += amt
                        if note:
                            daily_notes[d_obj].append(f"{note} (฿{amt:,.0f})")
                    elif tx_type == "Income" and cat == "Friend_Repay":
                        if "คอนโด" not in note_l and "rent" not in note_l and "ค่าเช่า" not in note_l:
                            daily_repay[d_obj] += amt
            except:
                pass
                
    # Build table rows from start_date up to today_date
    cum_actual = 0.0
    rows_html = []
    
    # Iterate through dates up to today
    active_dates = [d.date() if isinstance(d, pd.Timestamp) else d for d in dates if (d.date() if isinstance(d, pd.Timestamp) else d) <= today_date]
    
    for idx, d_dt in enumerate(active_dates):
        g = daily_gross[d_dt]
        r = daily_repay[d_dt]
        net = max(0.0, g - r)
        cum_actual += net
        cum_ideal = (idx + 1) * base_daily
        diff = net - base_daily
        
        # Status badge
        if net == 0 and d_dt == today_date:
            badge = '<span style="background: #F1F5F9; color: #475569; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">⏳ ยังไม่เริ่มใช้</span>'
        elif diff <= 0:
            badge = f'<span style="background: #ECFDF5; color: #059669; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">🟢 ต่ำกว่างบ ฿{abs(diff):,.0f}</span>'
        else:
            badge = f'<span style="background: #FEF2F2; color: #DC2626; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">🔴 เกินงบ ฿{diff:,.0f}</span>'
            
        repay_str = f'<span style="color: #059669; font-size: 11px;">-฿{r:,.0f}</span>' if r > 0 else '<span style="color: #94A3B8;">-</span>'
        gross_str = f'฿{g:,.0f}' if g > 0 else '<span style="color: #94A3B8;">฿0</span>'
        net_str = f'<b style="color: #0F172A;">฿{net:,.0f}</b>' if net > 0 else '<span style="color: #64748B;">฿0</span>'
        
        # Cumulative difference
        cum_diff = cum_actual - cum_ideal
        cum_diff_str = f'<span style="color: #059669; font-weight: 600;">(-฿{abs(cum_diff):,.0f})</span>' if cum_diff <= 0 else f'<span style="color: #DC2626; font-weight: 600;">(+฿{cum_diff:,.0f})</span>'
        
        is_today_row = "background: #F8FAFC; font-weight: 600;" if d_dt == today_date else ""
        date_label = f"{d_dt.strftime('%d %b')} " + ("<span style='color: #2563EB; font-size: 11px;'>(วันนี้)</span>" if d_dt == today_date else f"(Day {idx+1})")
        
        rows_html.append(
            f'<tr style="{is_today_row} border-bottom: 1px solid #F1F5F9;">'
            f'<td style="padding: 9px 12px; white-space: nowrap;">{date_label}</td>'
            f'<td style="padding: 9px 12px; text-align: right; color: #64748B;">{gross_str}</td>'
            f'<td style="padding: 9px 12px; text-align: right;">{repay_str}</td>'
            f'<td style="padding: 9px 12px; text-align: right;">{net_str}</td>'
            f'<td style="padding: 9px 12px; text-align: center;">{badge}</td>'
            f'<td style="padding: 9px 12px; text-align: right; white-space: nowrap;">฿{cum_actual:,.0f} <span style="font-size: 11px; color: #64748B;">/ {cum_ideal:,.0f}</span> {cum_diff_str}</td>'
            f'</tr>'
        )
        
    table_content = "".join(rows_html)
    
    total_cum_ideal = len(active_dates) * base_daily
    net_saved = total_cum_ideal - cum_actual
    summary_badge = f"🎉 ประหยัดสะสม ฿{net_saved:,.0f} (Under Budget)" if net_saved >= 0 else f"⚠️ เกินงบสะสม ฿{abs(net_saved):,.0f}"
    summary_color = "#059669" if net_saved >= 0 else "#DC2626"
    
    html_output = (
        f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 14px 16px; margin-top: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">'
        f'<div style="font-size: 13.5px; font-weight: 700; color: #0F172A;">📋 ตารางสรุปการใช้จ่ายค่าอาหารรายวัน (Daily Food Pacing Breakdown)</div>'
        f'<div style="font-size: 12px; font-weight: 700; color: {summary_color}; background: #F8FAFC; padding: 3px 10px; border-radius: 8px; border: 1px solid #E2E8F0;">{summary_badge}</div>'
        f'</div>'
        f'<div style="overflow-x: auto;">'
        f'<table style="width: 100%; border-collapse: collapse; font-size: 12px; font-family: \'Prompt\', \'Inter\', sans-serif;">'
        f'<thead>'
        f'<tr style="background: #F8FAFC; border-bottom: 1.5px solid #CBD5E1; color: #475569; font-size: 11.5px; text-transform: uppercase;">'
        f'<th style="padding: 8px 12px; text-align: left;">📅 วันที่</th>'
        f'<th style="padding: 8px 12px; text-align: right;">เต็มบิล (Gross)</th>'
        f'<th style="padding: 8px 12px; text-align: right;">เพื่อนคืน (Repay)</th>'
        f'<th style="padding: 8px 12px; text-align: right;">กินจริง (Net)</th>'
        f'<th style="padding: 8px 12px; text-align: center;">สถานะงบวัน (฿350)</th>'
        f'<th style="padding: 8px 12px; text-align: right;">สะสมจริง vs เป้าหมาย</th>'
        f'</tr>'
        f'</thead>'
        f'<tbody>{table_content}</tbody>'
        f'</table>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html_output, unsafe_allow_html=True)




