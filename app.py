"""
Personal Finance Tracking Web Application
Streamlit + Google Sheets (gspread) Backend + 4-Account Double-Entry Engine
Project 27: Money Management (23rd - 22nd Financial Cycle)
"""

import os
import json
from datetime import date, datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config
from cycle_utils import get_cycle_for_date, get_current_cycle_info
from backend import FinanceBackend
from transaction_engine import TransactionEngine
import ui_components

# Streamlit Page Config
st.set_page_config(
    page_title="Financial Cockpit | Money Management",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom CSS
ui_components.inject_styles()

# Initialize Session State & Backend Engine
if "backend" not in st.session_state:
    st.session_state.backend = FinanceBackend()

if "engine" not in st.session_state:
    st.session_state.engine = TransactionEngine(st.session_state.backend)

backend: FinanceBackend = st.session_state.backend
engine: TransactionEngine = st.session_state.engine

# Real-time summaries
summary = engine.get_accounts_summary()
cycle_analytics = engine.get_cycle_analytics()
cycle_info = cycle_analytics["cycle_info"]

# -------------------------------------------------------------
# SIDEBAR: Quick Actions & Transaction Entry
# -------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚡ Fast Macros (ปุ่มลัดอัตโนมัติ)")
    
    with st.expander("🚀 ดำเนินการประจำสัปดาห์ / เดือน", expanded=True):
        if st.button("⚡ จัดสรรงบสัปดาห์ (3,150฿)\nThai Credit ➡️ SCB", use_container_width=True):
            engine.macro_weekly_allowance()
            st.success("✅ โอนงบสัปดาห์ 3,150฿ (อาหาร 2,450 + เดินทาง 700) เรียบร้อย!")
            st.rerun()

        if st.button("🚆 แตะบัตรเดินทาง BTS/MRT (700฿)\nSCB ➡️ KBANK", use_container_width=True):
            engine.macro_transit_swipe()
            st.success("✅ สำรองเงินค่าเดินทางเข้า KBANK 700฿ (Zero CC Debt) เรียบร้อย!")
            st.rerun()

        kbank_current_buffer = summary.get("kbank_balance", 0.0)
        if st.button(f"💳 จ่ายบิลบัตรเครดิต (฿{kbank_current_buffer:,.0f})\nKBANK ➡️ ชำระบิลบัตร", use_container_width=True):
            if kbank_current_buffer > 0:
                engine.macro_pay_credit_card_bill(amount=kbank_current_buffer)
                st.success(f"✅ ตัดชำระบิลบัตรเครดิต ฿{kbank_current_buffer:,.2f} ออกจาก KBANK เรียบร้อย!")
                st.rerun()
            else:
                st.warning("⚠️ ยอดเงินใน KBANK เป็น 0 (ไม่มีรายการค้างชำระ)")

        if st.button("🛡️ โอนเงินสำรองประกัน (3,500฿)\nThai Credit ➡️ BAY", use_container_width=True):
            engine.macro_insurance_sinking()
            st.success("✅ โอนเงินสำรองประกันเข้า BAY 3,500฿ เรียบร้อย!")
            st.rerun()

        if st.button("💰 บันทึกเงินเดือนเข้า 23rd (43,000฿)\nIncome ➡️ Thai Credit", use_container_width=True):
            engine.macro_salary_income()
            st.success("✅ บันทึกเงินเดือน 43,000฿ เข้า Thai Credit เรียบร้อย!")
            st.rerun()

    with st.expander("👥 รูดบัตรหารกับเพื่อน (Split Bill)", expanded=False):
        st.caption("เมื่อรูดบัตรเต็มจำนวนแทนเพื่อน ให้โอนเฉพาะส่วนของเราเข้า KBANK และเมื่อเพื่อนโอนคืนให้เอาเข้า KBANK เพื่อให้ยอดรอตัดบัตรครบพอดี")
        split_total = st.number_input("ยอดรูดบัตรรวม (Total Swiped ฿)", min_value=0.0, step=50.0, value=150.0, format="%.2f", key="split_tot")
        split_my_share = st.number_input("ส่วนของเรา (My Share ฿)", min_value=0.0, step=10.0, value=50.0, format="%.2f", key="split_my")
        split_friends_share = max(0.0, split_total - split_my_share)
        st.markdown(f"👥 เพื่อนต้องโอนคืน: <b style='color: #2563EB;'>฿{split_friends_share:,.2f}</b>", unsafe_allow_html=True)
        
        split_cat = st.selectbox(
            "หมวดหมู่งบของเรา:",
            options=["Food_Daily", "Special_Meal", "Other"],
            format_func=lambda x: config.CATEGORIES[x]["label"],
            key="split_c"
        )
        
        if st.button("⚡ บันทึกรูดบัตร (SCB ➡️ KBANK)", use_container_width=True, key="split_btn"):
            if split_my_share > 0:
                backend.add_transaction(
                    date_val=date.today(),
                    tx_type="Internal_Transfer",
                    from_account="SCB",
                    to_account="KBANK",
                    category=split_cat,
                    amount=split_my_share,
                    note=f"👥 รูดบัตรยอดรวม ฿{split_total:,.2f} (ส่วนของเรา ฿{split_my_share:,.2f} + เพื่อน ฿{split_friends_share:,.2f})"
                )
                st.success(f"✅ สำรองส่วนของเรา ฿{split_my_share:,.2f} เข้า KBANK เรียบร้อย!\n(เมื่อเพื่อนโอน ฿{split_friends_share:,.2f} คืนมา ให้โอนเข้า KBANK ยอดจะครบ ฿{split_total:,.2f} พอดีตัดบิลครับ)")
                st.rerun()

    st.markdown("---")
    st.markdown("### ✍️ บันทึกรายการใหม่ (New Transaction)")

    with st.form("new_transaction_form", clear_on_submit=True):
        tx_type = st.selectbox(
            "ประเภทรายการ (Type)",
            options=config.TRANSACTION_TYPES,
            format_func=lambda x: {
                "Expense": "🔴 โอนจ่ายภายนอก (Expense)",
                "Internal_Transfer": "🔄 โอนย้ายภายใน (Internal Transfer)",
                "Income": "🟢 รายรับ (Income)",
                "Adjustment": "⚙️ ปรับปรุงยอด (Adjustment)"
            }.get(x, x)
        )

        col_acc1, col_acc2 = st.columns(2)
        with col_acc1:
            from_acc = st.selectbox(
                "จากบัญชี (From)",
                options=[""] + config.ACCOUNT_NAMES,
                index=2 if tx_type == "Expense" else 1, # Default SCB for expense, Thai Credit for transfer
                format_func=lambda x: f"{config.ACCOUNTS[x]['icon']} {x}" if x in config.ACCOUNTS else "— ไม่ระบุ —"
            )
        with col_acc2:
            to_acc = st.selectbox(
                "ไปยังบัญชี (To)",
                options=[""] + config.ACCOUNT_NAMES,
                index=3 if tx_type == "Internal_Transfer" else 0, # Default KBANK for transfer
                format_func=lambda x: f"{config.ACCOUNTS[x]['icon']} {x}" if x in config.ACCOUNTS else "— ภายนอก / รายจ่าย —"
            )

        cat_choice = st.selectbox(
            "หมวดหมู่ (Category)",
            options=config.CATEGORY_NAMES,
            index=0 if tx_type == "Expense" else 9 if tx_type == "Income" else 11,
            format_func=lambda x: config.CATEGORIES.get(x, {}).get("label", x)
        )

        amount_val = st.number_input("จำนวนเงิน (THB)", min_value=0.0, step=50.0, format="%.2f")

        tx_date = st.date_input("วันที่ทำรายการ (Date)", value=date.today())
        note_val = st.text_input("บันทึกเพิ่มเติม (Note)", placeholder="เช่น มื้อเที่ยง, ค่าไฟหอพัก, รูดบัตรซื้อของ")

        submitted = st.form_submit_button("💾 บันทึกรายการ (Save Transaction)", use_container_width=True)

        if submitted:
            if amount_val <= 0:
                st.error("⚠️ กรุณาระบุจำนวนเงินมากกว่า 0")
            elif tx_type == "Expense" and not from_acc:
                st.error("⚠️ รายจ่ายต้องระบุบัญชีต้นทาง (From Account)")
            elif tx_type == "Internal_Transfer" and (not from_acc or not to_acc or from_acc == to_acc):
                st.error("⚠️ การโอนภายในต้องระบุบัญชีต้นทางและปลายทางที่ต่างกัน")
            else:
                backend.add_transaction(
                    date_val=tx_date,
                    tx_type=tx_type,
                    from_account=from_acc if from_acc else None,
                    to_account=to_acc if to_acc else None,
                    category=cat_choice,
                    amount=amount_val,
                    note=note_val
                )
                st.success(f"✅ บันทึกรายการ ฿{amount_val:,.2f} เรียบร้อย!")
                st.rerun()

    # Cloud Sync status badge
    st.markdown("---")
    if backend.is_connected_to_sheets:
        st.markdown("🟢 **Google Sheets Connected**")
    else:
        st.markdown("🟡 **Local DB Mode** (พร้อมใช้งาน)")

# -------------------------------------------------------------
# MAIN CONTENT AREA
# -------------------------------------------------------------

# Hero Header
ui_components.render_hero_header(cycle_info, summary)

# Main Navigation Tabs
tab_dash, tab_ledgers, tab_wishlist, tab_settings = st.tabs([
    "📊 ภาพรวมการเงิน (Main Dashboard)",
    "🏦 สมุดบัญชีและสเตทเมนต์ (Account Ledgers)",
    "🎁 เป้ารางวัล & Wishlist (Wishlist Tracker)",
    "⚙️ ตั้งค่าเงินเริ่มต้น & Google Sheets (Setup & Sync)"
])

# =============================================================
# TAB 1: MAIN DASHBOARD
# =============================================================
with tab_dash:
    # 4 KPI Summary Cards
    ui_components.render_kpi_cards(summary, cycle_analytics)
    
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    
    # 4 Account Balances Visual Row
    st.markdown("#### 🏛️ ยอดเงินคงเหลือแยกรายบัญชี (4 Core Accounts)")
    ui_components.render_account_cards(summary["accounts"])

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Charts Row: Food Burn Rate & Category Donut
    col_chart1, col_chart2 = st.columns([3, 2])
    
    with col_chart1:
        transactions = backend.get_transactions()
        food_chart = ui_components.plot_daily_food_burn_chart(cycle_info, cycle_analytics["food_metrics"], transactions)
        st.plotly_chart(food_chart, use_container_width=True)
        
    with col_chart2:
        donut_chart = ui_components.plot_category_spend_donut(cycle_analytics["category_spend"])
        st.plotly_chart(donut_chart, use_container_width=True)

    # Envelope & Budget Execution Section
    st.markdown("#### 🎯 ติดตามภาระผูกพันประจำงวด (Fixed Commitments & Envelopes)")
    
    col_env1, col_env2, col_env3, col_env4, col_env5 = st.columns(5)
    
    # 1. Mom
    mom_stat = cycle_analytics["fixed_status"]["Mom"]
    with col_env1:
        status_badge = "✅ จ่ายแล้ว" if mom_stat["done"] else "⏳ รอจ่าย (23rd)"
        badge_cls = "badge-emerald" if mom_stat["done"] else "badge-amber"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">❤️ ให้คุณแม่ (Mom)</div>
            <div style="font-size: 18px; font-weight: 700;">฿{mom_stat['spent']:,.0f} / 5,000</div>
            <div style="margin-top: 8px;"><span class="badge-pill {badge_cls}">{status_badge}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # 2. DCA Investment
    dca_stat = cycle_analytics["fixed_status"]["DCA"]
    with col_env2:
        status_badge = "✅ ลงทุนแล้ว" if dca_stat["done"] else "⏳ รอตัด DCA"
        badge_cls = "badge-emerald" if dca_stat["done"] else "badge-amber"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📈 DCA ลงทุน</div>
            <div style="font-size: 18px; font-weight: 700;">฿{dca_stat['spent']:,.0f} / 4,800</div>
            <div style="margin-top: 8px;"><span class="badge-pill {badge_cls}">{status_badge}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Insurance Fund Transfer
    ins_stat = cycle_analytics["insurance_status"]
    with col_env3:
        status_badge = "✅ โอนเข้า BAY แล้ว" if ins_stat["done"] else "⏳ รอโอน (23rd)"
        badge_cls = "badge-emerald" if ins_stat["done"] else "badge-amber"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🛡️ สำรองประกัน (BAY)</div>
            <div style="font-size: 18px; font-weight: 700;">฿{ins_stat['funded']:,.0f} / 3,500</div>
            <div style="margin-top: 8px;"><span class="badge-pill {badge_cls}">{status_badge}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # 4. Rent
    rent_stat = cycle_analytics["fixed_status"]["Rent"]
    with col_env4:
        status_badge = "✅ จ่ายแล้ว" if rent_stat["done"] else "⏳ รอสิ้นเดือน"
        badge_cls = "badge-emerald" if rent_stat["done"] else "badge-amber"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🏠 ค่าเช่าห้อง (Rent)</div>
            <div style="font-size: 18px; font-weight: 700;">฿{rent_stat['spent']:,.0f} / 6,000</div>
            <div style="margin-top: 8px;"><span class="badge-pill {badge_cls}">{status_badge}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # 5. Utilities & Phone
    util_stat = cycle_analytics["fixed_status"]["Utilities_Phone"]
    with col_env5:
        status_badge = "✅ จ่ายแล้ว" if util_stat["done"] else "⏳ รอวันที่ 15"
        badge_cls = "badge-emerald" if util_stat["done"] else "badge-amber"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">⚡ ค่าน้ำ/ไฟ/โทรศัพท์</div>
            <div style="font-size: 18px; font-weight: 700;">฿{util_stat['spent']:,.0f} / 2,650</div>
            <div style="margin-top: 8px;"><span class="badge-pill {badge_cls}">{status_badge}</span></div>
        </div>
        """, unsafe_allow_html=True)

# =============================================================
# TAB 2: ACCOUNT LEDGERS & STATEMENTS
# =============================================================
with tab_ledgers:
    st.markdown("### 🏦 สมุดบัญชีและสเตทเมนต์รายบัญชี (Account Statements & Ledger)")
    
    selected_account = st.selectbox(
        "เลือกบัญชีที่ต้องการตรวจสอบสเตทเมนต์:",
        options=config.ACCOUNT_NAMES,
        format_func=lambda x: f"{config.ACCOUNTS[x]['icon']} {config.ACCOUNTS[x]['name']} (คงเหลือ ฿{summary['accounts'][x]['current_balance']:,.2f})"
    )
    
    statement_df = engine.get_account_statement(selected_account)
    
    if not statement_df.empty:
        # Running Balance Chart
        chart_data = statement_df.copy()
        chart_data["Date"] = pd.to_datetime(chart_data["Date"])
        chart_data = chart_data.sort_values(by="Date", ascending=True)
        
        fig_bal = go.Figure()
        fig_bal.add_trace(go.Scatter(
            x=chart_data["Date"],
            y=chart_data["Balance"],
            mode="lines+markers",
            name=f"ยอดคงเหลือ {selected_account}",
            line=dict(color=config.ACCOUNTS[selected_account]["color"], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.05)"
        ))
        fig_bal.update_layout(
            title=f"📊 เส้นทางยอดเงินคงเหลือ (Running Balance) - {selected_account}",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=dict(color="#334155", family="Prompt, Inter", size=12),
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0"),
            yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="ยอดคงเหลือ (THB)"),
            height=280
        )
        st.plotly_chart(fig_bal, use_container_width=True)

        # Statement Table
        st.markdown("##### 📜 รายการเดินบัญชี (Statement Records)")
        
        display_df = statement_df[["Date", "Type", "Description", "Inflow", "Outflow", "Balance", "Note", "Transaction_ID"]].copy()
        
        st.dataframe(
            display_df.style.format({
                "Inflow": lambda x: f"+฿{x:,.2f}" if x > 0 else "-",
                "Outflow": lambda x: f"-฿{x:,.2f}" if x > 0 else "-",
                "Balance": lambda x: f"฿{x:,.2f}"
            }),
            use_container_width=True,
            height=350
        )
        
        # Delete Transaction Option
        with st.expander("🗑️ ลบรายการที่ไม่ต้องการ (Delete Transaction)"):
            tx_ids = [t for t in display_df["Transaction_ID"].tolist() if t != "INITIAL"]
            if tx_ids:
                selected_del = st.selectbox("เลือก Transaction ID ที่ต้องการลบ:", options=tx_ids)
                if st.button("❌ ยืนยันการลบรายการนี้", type="secondary"):
                    if backend.delete_transaction(selected_del):
                        st.success(f"✅ ลบรายการ {selected_del} เรียบร้อยแล้ว")
                        st.rerun()
            else:
                st.info("ไม่มีรายการที่สามารถลบได้ (ไม่รวมยอดเงินเริ่มต้น)")
    else:
        st.info(f"ยังไม่มีรายการเคลื่อนไหวสำหรับบัญชี {selected_account}")

# =============================================================
# TAB 3: WISHLIST TRACKER
# =============================================================
with tab_wishlist:
    st.markdown("### 🎁 เป้าหมายของรางวัลและไลฟ์สไตล์ (Wishlist Tracker)")
    st.caption("วางแผนซื้อของรางวัลชีวิตโดยไม่กระทบงบหลัก พร้อมบันทึกการตัดจ่ายเมื่อซื้อสำเร็จ")

    wishlist_items = backend.get_wishlist()
    
    col_w1, col_w2 = st.columns([3, 2])
    
    with col_w1:
        st.markdown("#### 🛍️ รายการของที่อยากได้ (Wishlist Items)")
        
        for idx, item in enumerate(wishlist_items):
            target_price = float(item.get("Target_Price", 0.0))
            saved_amt = float(item.get("Current_Saved", 0.0))
            status = item.get("Status", "Pending")
            pct = min(100, int((saved_amt / target_price) * 100)) if target_price > 0 else 0
            
            with st.container():
                st.markdown(f"""
                <div class="account-card" style="margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 16px; font-weight: 700; color: #FFFFFF;">🎁 {item['Item_Name']}</span>
                        <span class="badge-pill {'badge-emerald' if status == 'Purchased' else 'badge-purple'}">{status} • {item.get('Priority', 'Medium')} Priority</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 14px;">
                        <span style="color: #9CA3AF;">เป้าหมาย: {item.get('Target_Month', '2026-09')}</span>
                        <span style="font-weight: 700; color: #34D399;">฿{saved_amt:,.0f} / ฿{target_price:,.0f} ({pct}%)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.progress(pct / 100)
                
                # Action Buttons for Wishlist Item
                col_btn1, col_btn2 = st.columns([1, 2])
                with col_btn1:
                    if status != "Purchased":
                        if st.button(f"💳 ซื้อแล้ว (฿{target_price:,.0f})", key=f"buy_wish_{idx}"):
                            # Log transaction as Wishlist expense from SCB or Thai Credit
                            backend.add_transaction(
                                date_val=date.today(),
                                tx_type="Expense",
                                from_account="SCB",
                                to_account=None,
                                category="Wishlist_Hobby",
                                amount=target_price,
                                note=f"🎁 ซื้อของรางวัลชีวิต: {item['Item_Name']}"
                            )
                            # Update status to Purchased
                            wishlist_items[idx]["Status"] = "Purchased"
                            wishlist_items[idx]["Current_Saved"] = target_price
                            backend.save_wishlist(wishlist_items)
                            st.success(f"🎉 ยินดีด้วย! บันทึกการซื้อ {item['Item_Name']} เรียบร้อยแล้ว")
                            st.rerun()
                st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

    with col_w2:
        st.markdown("#### ➕ เพิ่มเป้าหมาย Wishlist ใหม่")
        with st.form("new_wishlist_item_form", clear_on_submit=True):
            new_item_name = st.text_input("ชื่อสิ่งของ / รางวัล", placeholder="เช่น หูฟังไร้สาย, รองเท้าผ้าใบ")
            new_price = st.number_input("ราคาเป้าหมาย (THB)", min_value=100.0, step=100.0, value=2500.0)
            new_month = st.text_input("เดือนเป้าหมาย (Target Month)", value=date.today().strftime("%Y-%m"))
            new_priority = st.selectbox("ลำดับความสำคัญ (Priority)", options=["High", "Medium", "Low"], index=1)
            new_saved = st.number_input("เงินที่เก็บสะสมไว้แล้ว (THB)", min_value=0.0, step=100.0, value=0.0)
            
            wish_submit = st.form_submit_button("✨ เพิ่มเข้า Wishlist", use_container_width=True)
            if wish_submit:
                if new_item_name.strip():
                    wishlist_items.append({
                        "Item_Name": new_item_name.strip(),
                        "Target_Price": float(new_price),
                        "Target_Month": new_month,
                        "Priority": new_priority,
                        "Status": "In Progress" if new_saved > 0 else "Pending",
                        "Current_Saved": float(new_saved)
                    })
                    backend.save_wishlist(wishlist_items)
                    st.success(f"✅ เพิ่ม {new_item_name} เข้า Wishlist เรียบร้อยแล้ว!")
                    st.rerun()
                else:
                    st.error("⚠️ กรุณาระบุชื่อสิ่งของ")

# =============================================================
# TAB 4: SETUP INITIAL BALANCES & GOOGLE SHEETS SYNC
# =============================================================
with tab_settings:
    st.markdown("### ⚙️ การตั้งค่ายอดเงินเริ่มต้น & การเชื่อมต่อ Google Sheets")

    # Section 1: Initial Balances Editor
    st.markdown("#### 🏁 1. ตั้งค่ายอดเงินเริ่มต้นคงเหลือแต่ละบัญชี (Initial Leftover Balances)")
    st.caption("กรอกยอดเงินจริงที่ค้างอยู่ในแต่ละบัญชี ณ วันเริ่มต้น เพื่อให้ระบบคำนวณยอดคงเหลือสุทธิ (Current Balance) อย่างแม่นยำ")

    accounts_data = backend.get_accounts()
    acc_initials = {a["Account_Name"]: float(a.get("Initial_Balance", 0.0)) for a in accounts_data}

    with st.form("initial_balance_form"):
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            init_thai_credit = st.number_input(
                f"🏛️ Thai Credit (HQ / Primary) - เงินต้นเริ่มต้น (THB)",
                min_value=0.0,
                step=500.0,
                value=acc_initials.get("Thai Credit", 15000.0),
                format="%.2f"
            )
            init_scb = st.number_input(
                f"💜 SCB (Daily Spending Wallet) - เงินต้นเริ่มต้น (THB)",
                min_value=0.0,
                step=100.0,
                value=acc_initials.get("SCB", 3150.0),
                format="%.2f"
            )
        with col_i2:
            init_kbank = st.number_input(
                f"💚 KBANK (CC Reserve Buffer) - เงินต้นเริ่มต้น (THB)",
                min_value=0.0,
                step=100.0,
                value=acc_initials.get("KBANK", 2000.0),
                format="%.2f"
            )
            init_bay = st.number_input(
                f"💛 BAY (Wealth Vault & Sinking Funds) - เงินต้นเริ่มต้น (THB)",
                min_value=0.0,
                step=1000.0,
                value=acc_initials.get("BAY", 50000.0),
                format="%.2f"
            )

        save_inits = st.form_submit_button("💾 บันทึกยอดเงินเริ่มต้น (Save Initial Balances)", use_container_width=True)
        if save_inits:
            new_inits = {
                "Thai Credit": init_thai_credit,
                "SCB": init_scb,
                "KBANK": init_kbank,
                "BAY": init_bay
            }
            backend.update_initial_balances(new_inits)
            st.success("✅ อัปเดตยอดเงินเริ่มต้นและคำนวณยอดเงินคงเหลือปัจจุบันเรียบร้อย!")
            st.rerun()

    with st.expander("🧹 จัดการล้างประวัติรายการธุรกรรม (Reset / Clear Transactions)"):
        st.caption("หากต้องการล้างรายการทดสอบทั้งหมดออก แล้วเริ่มบันทึกใหม่จากยอดเงินเริ่มต้นปัจจุบัน")
        if st.button("🗑️ ล้างรายการธุรกรรมทั้งหมด (Clear All Transactions)", type="secondary"):
            with backend.db._get_connection() as conn:
                conn.execute("DELETE FROM transactions")
                conn.commit()
            backend.recalculate_all_balances()
            st.success("✅ ล้างรายการธุรกรรมทั้งหมดเรียบร้อย! ยอดคงเหลือกลับมาเท่ากับยอดเริ่มต้นพอดี")
            st.rerun()

    st.markdown("---")

    st.markdown("---")

    # Section 2: Cloud Sync (Google Sheets & SQLite)
    st.markdown("#### ☁️ 2. เชื่อมต่อ Google Sheets (สำหรับบันทึกจากมือถือ & ซิงค์อัตโนมัติ)")
    st.caption("สามารถเลือกเชื่อมต่อด้วย Google Apps Script Web App (ง่ายที่สุด ใช้ Google Account ตัวเองได้ทันที) หรือ Service Account JSON")

    sync_method = st.radio(
        "เลือกวิธีเชื่อมต่อ Google Sheets:",
        options=["วิธีที่ 1: Google Apps Script Webhook (แนะนำ - ง่ายมาก ใช้ Gmail ตัวเองได้ทันที)", "วิธีที่ 2: Google Service Account JSON"],
        horizontal=True
    )

    col_gs1, col_gs2 = st.columns([3, 2])

    with col_gs1:
        if "วิธีที่ 1" in sync_method:
            st.markdown("##### 🚀 เชื่อมต่อด้วย Webhook URL (ไม่ต้องตั้งค่า Google Cloud)")
            
            curr_webhook = backend.webhook_url
            webhook_input = st.text_input(
                "วาง Google Apps Script Web App URL ที่นี่:",
                value=curr_webhook,
                placeholder="https://script.google.com/macros/s/.../exec"
            )
            
            col_wh1, col_wh2, col_wh3 = st.columns(3)
            with col_wh1:
                if st.button("🔗 บันทึก & เชื่อมต่อ", use_container_width=True):
                    if backend.set_webhook_url(webhook_input):
                        st.success("🎉 เชื่อมต่อ Google Sheets สำเร็จเรียบร้อย!")
                        st.rerun()
                    else:
                        st.error(f"❌ เชื่อมต่อไม่สำเร็จ: {backend.connection_error}")
                        
            with col_wh2:
                if st.button("⬆️ Push Data to Sheet", use_container_width=True):
                    if backend.sync_push_to_webhook():
                        st.success("✅ ส่งข้อมูลทั้งหมดขึ้น Google Sheets สำเร็จ!")
                    else:
                        st.error("⚠️ ไม่สามารถส่งข้อมูลได้ กรุณาตรวจสอบ URL")
                        
            with col_wh3:
                if st.button("⬇️ Pull Data from Sheet", use_container_width=True):
                    if backend.sync_pull_from_webhook():
                        st.success("✅ ดึงข้อมูลล่าสุดจาก Google Sheets สำเร็จ!")
                        st.rerun()
                    else:
                        st.error("⚠️ ไม่สามารถดึงข้อมูลได้ กรุณาตรวจสอบ URL")

            with st.expander("📖 วิธีตั้งค่า Google Apps Script (ทำครั้งเดียว 1 นาที)", expanded=False):
                st.markdown("""
                1. เปิด [Google Sheets](https://sheets.google.com) แล้วสร้างสเปรดชีตใหม่ (เช่น `Money_Management_2026`)
                2. เมนูด้านบน เลือก **Extensions (ส่วนขยาย) ➡️ Apps Script**
                3. ลบโค้ดเดิมทั้งหมด แล้ววางโค้ดด้านล่างนี้ลงไป:
                """)
                with open("apps_script_code.js", "r", encoding="utf-8") as f:
                    script_code = f.read()
                st.code(script_code, language="javascript")
                st.markdown("""
                4. กดปุ่ม **Deploy (การทำให้ใช้งานได้)** มุมขวาบน ➡️ เลือก **New deployment (การทำให้ใช้งานได้รายการใหม่)**
                5. เลือก Type: **Web app (เว็บแอป)**
                6. Execute as: **Me (ฉัน)** | Who has access: **Anyone (ทุกคน)**
                7. กด **Deploy** แล้ว Copy URL มาวางในช่องด้านบนนี้ได้เลยครับ!
                """)
        else:
            sheet_input = st.text_input(
                "ชื่อ Google Spreadsheet หรือ URL ของ Sheet",
                value=backend.sheet_title,
                help="สามารถใส่ชื่อไฟล์ Sheet เช่น Money_Management_2026 หรือ URL เต็มของ Google Sheet"
            )
            
            uploaded_creds = st.file_uploader(
                "📁 อัปโหลดไฟล์ Service Account JSON (ถ้ามี)",
                type=["json"],
                help="ดาวน์โหลด JSON จาก Google Cloud Console (IAM & Admin -> Service Accounts -> Keys)"
            )
            if uploaded_creds is not None:
                try:
                    creds_data = json.load(uploaded_creds)
                    with open("service_account.json", "w", encoding="utf-8") as f:
                        json.dump(creds_data, f, indent=2)
                    st.success("✅ อัปโหลดและบันทึก service_account.json สำเร็จ!")
                except Exception as e:
                    st.error(f"❌ ไฟล์ JSON ไม่ถูกต้อง: {e}")

            creds_file_path = st.text_input(
                "ตำแหน่งไฟล์ Service Account JSON",
                value="service_account.json",
                help="วางไฟล์ service_account.json ไว้ที่โฟลเดอร์โปรเจกต์ หรือระบุ path แบบ absolute"
            )

            if st.button("🔌 ทดสอบการเชื่อมต่อ Service Account", use_container_width=True):
                success = backend.connect_google_sheets(creds_path=creds_file_path, sheet_identifier=sheet_input)
                if success:
                    st.success("🎉 เชื่อมต่อ Google Sheets สำเร็จเรียบร้อย!")
                    st.rerun()
                else:
                    st.error(f"❌ ไม่สามารถเชื่อมต่อได้: {backend.connection_error}")

        st.markdown("---")
        st.markdown("##### 📱 บันทึกจากมือถือ (2 ช่องทาง):")
        st.markdown("""
        1. **เปิด Web Dashboard บนมือถือโดยตรง**:
           - เชื่อมต่อ Wi-Fi หรือ Hotspot เดียวกับคอมพิวเตอร์
           - เปิดเบราว์เซอร์ในมือถือพิมพ์: **`http://172.20.10.5:8501`**
           - กด *Add to Home Screen* เพื่อใช้งานเป็น Web App ได้ทันที
        2. **พิมพ์ในแอป Google Sheets บนมือถือ**:
           - บันทึกรายการลงในแท็บ `Transactions` ของ Google Sheet ในมือถือ
           - ข้อมูลจะ Sync กับแดชบอร์ดอัตโนมัติ
        """)

    with col_gs2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📡 สถานะการเชื่อมต่อ & ฐานข้อมูล</div>
            <div style="font-size: 18px; font-weight: 700; color: {'#34D399' if backend.is_connected_to_sheets else '#FBBF24'};">
                {'🟢 ออนไลน์ (Google Sheets Live Sync)' if backend.is_connected_to_sheets else '🟡 Local SQLite Database Mode'}
            </div>
            <div class="metric-sub" style="color: #9CA3AF; margin-top: 10px; line-height: 1.6;">
                🗄️ <b>Relational Engine:</b> SQLite (<code>data/finance.db</code>)<br>
                🔒 <b>Integrity:</b> ACID Compliant Double-Entry<br>
                ☁️ <b>Cloud Sync:</b> {'เชื่อมต่อแล้ว' if backend.is_connected_to_sheets else 'พร้อมเชื่อมต่อ Google Sheet'}
            </div>
        </div>
        """, unsafe_allow_html=True)
