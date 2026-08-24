"""
UI Components & Custom Styling Module (Clean Minimalist White Theme)
Clean, modern, high-contrast visual design with subtle accent indicators.
"""

import base64
import os
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
    actual_spent_by_date = {d: 0.0 for d in dates}
    if not df.empty and "Category" in df.columns:
        food_tx = df[(df["Type"] == "Expense") & (df["Category"] == "Food_Daily")].copy()
        if not food_tx.empty:
            food_tx["Date_Obj"] = pd.to_datetime(food_tx["Date"]).dt.date
            grouped = food_tx.groupby("Date_Obj")["Amount"].sum().to_dict()
            for d, amt in grouped.items():
                if d in actual_spent_by_date:
                    actual_spent_by_date[d] = amt
    
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
        name="งบตามแผน (฿350/day)",
        line=dict(color="#94A3B8", width=1.5, dash="dash")
    ))
    
    # Actual spend line
    fig.add_trace(go.Scatter(
        x=[d.strftime("%d %b") for d in dates],
        y=actual_cumulative,
        mode="lines+markers",
        name="จ่ายจริงสะสม (Actual Food)",
        line=dict(color="#DC2626" if food_metrics["pace_diff"] > 350 else "#059669", width=2.5),
        marker=dict(size=5)
    ))
    
    fig.update_layout(
        title="📈 การใช้จ่ายงบอาหารเทียบกับแผน (Food Burn Rate Pacing)",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#334155", family="Prompt, Inter", size=12),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0"),
        yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="บาท (THB)"),
        height=320
    )
    return fig

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


