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
        if st.button("⚡ จัดสรรงบสัปดาห์ (3,450฿)\nThai Credit ➡️ SCB", use_container_width=True):
            engine.macro_weekly_allowance()
            st.success("✅ โอนงบสัปดาห์ 3,450฿ (อาหาร 2,450 + เดินทาง 1,000) เรียบร้อย!")
            st.rerun()

        if st.button("🚆 แตะบัตรเดินทาง BTS/MRT (1,000฿)\nSCB ➡️ KBANK", use_container_width=True):
            engine.macro_transit_swipe()
            st.success("✅ สำรองเงินค่าเดินทางเข้า KBANK 1,000฿ (Zero CC Debt) เรียบร้อย!")
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

    with st.expander("💳 รูดบัตรไว้ก่อน (ยังไม่ได้โอนเข้า KBANK)", expanded=False):
        st.caption("บันทึกรายการที่รูดบัตรไปก่อน แต่ยังไม่มีเงินใน SCB หรือยังไม่ได้โอนเข้า KBANK ทันที รายการจะไปรอในแท็บ 'เงินค่าบัตรรอโอน'")
        p_quick_item = st.text_input("รายการที่รูด:", placeholder="เช่น ค่าดินเนอร์, เสื้อผ้า", key="sb_p_item")
        p_quick_amt = st.number_input("ยอดเงินที่รูด (฿):", min_value=0.0, step=50.0, value=300.0, format="%.2f", key="sb_p_amt")
        p_quick_cat = st.selectbox(
            "หมวดหมู่:",
            options=config.CATEGORY_NAMES,
            format_func=lambda x: config.CATEGORIES[x]["label"],
            key="sb_p_cat"
        )
        if st.button("➕ บันทึกรอโอนเข้า KBANK", use_container_width=True, key="sb_p_btn"):
            if p_quick_item.strip() and p_quick_amt > 0:
                backend.add_pending_cc(
                    date_val=date.today(),
                    item_name=p_quick_item.strip(),
                    category=p_quick_cat,
                    amount=p_quick_amt,
                    note="บันทึกด่วนจากแถบข้าง (รอโอนเข้า KBANK)"
                )
                st.success(f"✅ บันทึก '{p_quick_item.strip()}' ฿{p_quick_amt:,.2f} รอโอนเรียบร้อย!")
                st.rerun()
            else:
                st.error("กรุณาระบุรายการและจำนวนเงิน")

    st.markdown("---")
    st.markdown("### ✍️ บันทึกรายการใหม่ (New Transaction)")

    def _acc_label(x):
        return f"{config.ACCOUNTS[x]['icon']} {x}" if x in config.ACCOUNTS else "— ไม่ระบุ —"

    # Kept OUTSIDE the form: widgets inside st.form only rerun on submit, so putting the
    # type choice there meant the From/To fields below it were always one click stale.
    tx_type = st.radio(
        "เลือกประเภทรายการ (Choose transaction type)",
        options=["Expense", "Internal_Transfer", "Income", "Adjustment"],
        format_func=lambda x: {
            "Expense": "🔴 จ่ายออก (Pay out)",
            "Internal_Transfer": "🔄 โอนภายในบัญชี (Transfer)",
            "Income": "🟢 รายรับ (Income)",
            "Adjustment": "⚙️ ปรับยอด (Adjustment)"
        }.get(x, x),
        horizontal=True,
        key="new_tx_type"
    )

    with st.form("new_transaction_form", clear_on_submit=True):
        to_acc = None
        from_acc = None

        if tx_type == "Expense":
            from_acc = st.selectbox("จ่ายออกจากบัญชี (Pay from)", options=config.ACCOUNT_NAMES, index=1, format_func=_acc_label)
            default_cat = "Food_Daily"

        elif tx_type == "Internal_Transfer":
            col_acc1, col_acc2 = st.columns(2)
            with col_acc1:
                from_acc = st.selectbox("จากบัญชี (From)", options=config.ACCOUNT_NAMES, index=0, format_func=_acc_label)
            with col_acc2:
                to_acc = st.selectbox("ไปยังบัญชี (To)", options=config.ACCOUNT_NAMES, index=1, format_func=_acc_label)
            default_cat = "Other"

        elif tx_type == "Income":
            to_acc = st.selectbox("รับเข้าบัญชี (Deposit to)", options=config.ACCOUNT_NAMES, index=0, format_func=_acc_label)
            default_cat = "Salary"

        else:  # Adjustment
            col_acc1, col_acc2 = st.columns(2)
            with col_acc1:
                from_acc = st.selectbox("หักออกจากบัญชี (Decrease, optional)", options=[""] + config.ACCOUNT_NAMES, format_func=_acc_label)
            with col_acc2:
                to_acc = st.selectbox("เพิ่มเข้าบัญชี (Increase, optional)", options=[""] + config.ACCOUNT_NAMES, format_func=_acc_label)
            default_cat = "Other"

        cat_choice = st.selectbox(
            "หมวดหมู่ (Category)",
            options=config.CATEGORY_NAMES,
            index=config.CATEGORY_NAMES.index(default_cat),
            format_func=lambda x: config.CATEGORIES.get(x, {}).get("label", x)
        )

        amount_val = st.number_input("จำนวนเงิน (THB)", min_value=0.0, step=50.0, format="%.2f")

        tx_date = st.date_input("วันที่ทำรายการ (Date)", value=date.today())
        note_val = st.text_input("บันทึกเพิ่มเติม (Note)", placeholder="เช่น มื้อเที่ยง, ค่าไฟหอพัก, รูดบัตรซื้อของ")

        submitted = st.form_submit_button("💾 บันทึกรายการ (Save Transaction)", use_container_width=True, type="primary")

        if submitted:
            if amount_val <= 0:
                st.error("⚠️ กรุณาระบุจำนวนเงินมากกว่า 0")
            elif tx_type == "Internal_Transfer" and from_acc == to_acc:
                st.error("⚠️ การโอนภายในต้องระบุบัญชีต้นทางและปลายทางที่ต่างกัน")
            elif tx_type == "Adjustment" and not from_acc and not to_acc:
                st.error("⚠️ การปรับยอดต้องระบุบัญชีที่จะเพิ่มหรือหักอย่างน้อยหนึ่งบัญชี")
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
tab_dash, tab_pending_cc, tab_ledgers, tab_wishlist, tab_settings = st.tabs([
    "📊 ภาพรวมการเงิน (Main Dashboard)",
    "💳 เงินค่าบัตรรอโอน (Pending CC)",
    "🏦 สมุดบัญชีและสเตทเมนต์ (Account Ledgers)",
    "🎁 เป้ารางวัล & Wishlist (Wishlist Tracker)",
    "⚙️ ตั้งค่าเงินเริ่มต้น & Google Sheets (Setup & Sync)"
])

# =============================================================
# TAB 1: MAIN DASHBOARD
# =============================================================
with tab_dash:
    # 0. Credit Card Due Date Alert Banner (if any card is due <= 5 days)
    cc_summary = engine.get_credit_cards_summary()
    ui_components.render_due_credit_card_alerts(cc_summary)

    # 1. 4 KPI Summary Cards
    ui_components.render_kpi_cards(summary, cycle_analytics)
    
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 2. Daily Expense Summary Section (Today's Expenses & Food Pacing)
    st.markdown("#### 📅 สรุปค่าใช้จ่ายประจำวัน (Today's Expense & Daily Pacing)")
    today_summary = engine.get_today_summary()
    ui_components.render_today_expense_summary(today_summary)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    
    # 3. 4 Account Balances Visual Row
    st.markdown("#### 🏛️ ยอดเงินคงเหลือแยกรายบัญชี (4 Core Accounts)")
    ui_components.render_account_cards(summary["accounts"])

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)


    # Charts Row: Switcher between Food Pacing vs Monthly Expense & Surplus Tracker
    st.markdown("#### 📈 แทรคสถานะการเงิน & ความเร็วการใช้จ่าย (Financial Burn & Pacing)")
    
    track_view = st.radio(
        "เลือกมุมมองการแทรค (Select Tracker View):",
        options=["🍚 แทรคงบอาหารประจำวัน (Daily Food Pacing)", "📊 แทรคภาพรวมค่าใช้จ่าย & เป้าหมายเงินเหลือ (Monthly Expense & Surplus Target)"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    col_chart1, col_chart2 = st.columns([3, 2])
    
    transactions = backend.get_transactions()
    cycle_plan = backend.get_cycle_plan(cycle_info["cycle_id"])

    with col_chart1:
        if "Food Pacing" in track_view:
            food_chart = ui_components.plot_daily_food_burn_chart(cycle_info, cycle_analytics["food_metrics"], transactions)
            st.plotly_chart(food_chart, use_container_width=True, config={"displayModeBar": False})
            ui_components.render_daily_food_pacing_table(cycle_info, transactions)
        else:
            monthly_tracker_res = ui_components.plot_monthly_expense_surplus_tracker(
                cycle_info, cycle_plan, transactions, cycle_analytics
            )
            st.plotly_chart(monthly_tracker_res["fig"], use_container_width=True, config={"displayModeBar": False})
            
            # Mini KPI indicators for Monthly Plan
            p_inc = monthly_tracker_res["planned_income"]
            t_sur = monthly_tracker_res["target_surplus"]
            p_exp = monthly_tracker_res["planned_expense"]
            c_tot = monthly_tracker_res["current_actual_total"]
            proj_sur = monthly_tracker_res["projected_surplus"]
            
            status_color = "#059669" if proj_sur >= t_sur else ("#D97706" if proj_sur >= 0 else "#DC2626")
            status_badge = "🟢 เป็นไปตามเป้าหมาย (On Track)" if proj_sur >= t_sur else ("🟡 ใช้จ่ายเร็วกว่าแผนเล็กน้อย" if proj_sur >= 0 else "🔴 เสี่ยงติดลบ")
            
            st.markdown(f"""
            <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 12px 16px; margin-top: -10px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <div>
                        <div style="font-size: 11.5px; color: #64748B; text-transform: uppercase;">💰 เงินเข้าตามแผนงวดนี้</div>
                        <div style="font-size: 15px; font-weight: 700; color: #0F172A;">฿{p_inc:,.2f}</div>
                    </div>
                    <div>
                        <div style="font-size: 11.5px; color: #64748B; text-transform: uppercase;">🎯 เป้าหมายเงินเหลือสิ้นเดือน</div>
                        <div style="font-size: 15px; font-weight: 700; color: #2563EB;">฿{t_sur:,.2f}</div>
                    </div>
                    <div>
                        <div style="font-size: 11.5px; color: #64748B; text-transform: uppercase;">💸 จ่ายสะสมถึงวันนี้</div>
                        <div style="font-size: 15px; font-weight: 700; color: #475569;">฿{c_tot:,.2f} / {p_exp:,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size: 11.5px; color: #64748B; text-transform: uppercase;">🔮 ประมาณการเงินเหลือสิ้นเดือน</div>
                        <div style="font-size: 15px; font-weight: 700; color: {status_color};">฿{proj_sur:,.2f} ({status_badge})</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Interactive Plan Editor Expander
            with st.expander("⚙️ ปรับแผนเงินเข้า & เป้าหมายเงินเหลือสำหรับงวดนี้ (Edit Monthly Plan)"):
                col_pl1, col_pl2 = st.columns(2)
                with col_pl1:
                    new_planned_inc = st.number_input(
                        "💰 เงินเดือน / เงินเข้าเดือนนี้ (Planned Inflow THB):",
                        min_value=1000.0, step=1000.0,
                        value=float(p_inc), format="%.2f"
                    )
                with col_pl2:
                    new_target_sur = st.number_input(
                        "🎯 เป้าหมายเงินเหลือสุทธิสิ้นเดือน (Target Surplus THB):",
                        min_value=0.0, step=500.0,
                        value=float(t_sur), format="%.2f"
                    )
                plan_note = st.text_input("📝 บันทึกแผนงวดนี้ (Note / Context):", value=cycle_plan.get("note", ""))
                
                if st.button("💾 บันทึกแผนงวดนี้ (Save Cycle Plan)", type="primary"):
                    backend.save_cycle_plan(cycle_info["cycle_id"], new_planned_inc, new_target_sur, plan_note)
                    st.success("✅ บันทึกแผนการเงินประจำงวดเรียบร้อยแล้ว!")
                    st.rerun()

    with col_chart2:
        donut_chart = ui_components.plot_category_spend_donut(cycle_analytics["category_spend"])
        st.plotly_chart(donut_chart, use_container_width=True, config={"displayModeBar": False})

    # Envelope & Budget Execution Section
    if "selected_envelope" not in st.session_state:
        st.session_state["selected_envelope"] = None

    cycle_df = cycle_analytics.get("cycle_df", pd.DataFrame())

    def get_envelope_txs(key):
        if cycle_df.empty:
            return pd.DataFrame()
        if key == "Mom":
            return cycle_df[(cycle_df["Category"] == "Mom")]
        elif key == "DCA":
            return cycle_df[(cycle_df["Category"] == "DCA")]
        elif key == "Insurance":
            return cycle_df[(cycle_df["Category"] == "Insurance_Fund") | ((cycle_df["Type"] == "Internal_Transfer") & (cycle_df["To_Account"] == "BAY"))]
        elif key == "Rent":
            return cycle_df[(cycle_df["Category"] == "Rent")]
        elif key == "Utilities_Phone":
            return cycle_df[(cycle_df["Category"] == "Utilities_Phone")]
        return pd.DataFrame()

    mom_txs = get_envelope_txs("Mom")
    dca_txs = get_envelope_txs("DCA")
    ins_txs = get_envelope_txs("Insurance")
    rent_txs = get_envelope_txs("Rent")
    util_txs = get_envelope_txs("Utilities_Phone")

    st.markdown("#### 🎯 ติดตามภาระผูกพันประจำงวด (Fixed Commitments & Envelopes)")
    st.caption("💡 คลิกที่ปุ่ม **'🔍 ดู Txn'** ใต้การ์ดแต่ละใบเพื่อดูรายการธุรกรรมที่บันทึกตัดจ่ายจริงในงวดนี้")
    
    col_env1, col_env2, col_env3, col_env4, col_env5 = st.columns(5)
    
    # 1. Mom
    mom_stat = cycle_analytics["fixed_status"]["Mom"]
    with col_env1:
        status_badge = "✅ จ่ายแล้ว" if mom_stat["done"] else "⏳ รอจ่าย (23rd)"
        badge_cls = "badge-emerald" if mom_stat["done"] else "badge-amber"
        border_style = "border: 2px solid #2563EB; box-shadow: 0 4px 12px rgba(37,99,235,0.15);" if st.session_state["selected_envelope"] == "Mom" else ""
        st.markdown(f"""
        <div class="metric-card" style="{border_style}">
            <div class="metric-label">❤️ ให้คุณแม่ (Mom)</div>
            <div style="font-size: 18px; font-weight: 700;">฿{mom_stat['spent']:,.0f} / 5,000</div>
            <div style="margin-top: 8px;"><span class="badge-pill {badge_cls}">{status_badge}</span></div>
        </div>
        """, unsafe_allow_html=True)
        btn_txt = f"🔍 ดู Txn ({len(mom_txs)})" if not mom_txs.empty else "🔍 ดู Txn (0)"
        if st.button(btn_txt, key="btn_toggle_mom", use_container_width=True):
            st.session_state["selected_envelope"] = None if st.session_state["selected_envelope"] == "Mom" else "Mom"
            st.rerun()

    # 2. DCA Investment
    dca_stat = cycle_analytics["fixed_status"]["DCA"]
    with col_env2:
        status_badge = "✅ ลงทุนแล้ว" if dca_stat["done"] else "⏳ รอตัด DCA"
        badge_cls = "badge-emerald" if dca_stat["done"] else "badge-amber"
        border_style = "border: 2px solid #2563EB; box-shadow: 0 4px 12px rgba(37,99,235,0.15);" if st.session_state["selected_envelope"] == "DCA" else ""
        st.markdown(f"""
        <div class="metric-card" style="{border_style}">
            <div class="metric-label">📈 DCA ลงทุน</div>
            <div style="font-size: 18px; font-weight: 700;">฿{dca_stat['spent']:,.0f} / 4,800</div>
            <div style="margin-top: 8px;"><span class="badge-pill {badge_cls}">{status_badge}</span></div>
        </div>
        """, unsafe_allow_html=True)
        btn_txt = f"🔍 ดู Txn ({len(dca_txs)})" if not dca_txs.empty else "🔍 ดู Txn (0)"
        if st.button(btn_txt, key="btn_toggle_dca", use_container_width=True):
            st.session_state["selected_envelope"] = None if st.session_state["selected_envelope"] == "DCA" else "DCA"
            st.rerun()

    # 3. Insurance Fund Transfer
    ins_stat = cycle_analytics["insurance_status"]
    with col_env3:
        status_badge = "✅ โอนเข้า BAY แล้ว" if ins_stat["done"] else "⏳ รอโอน (23rd)"
        badge_cls = "badge-emerald" if ins_stat["done"] else "badge-amber"
        border_style = "border: 2px solid #2563EB; box-shadow: 0 4px 12px rgba(37,99,235,0.15);" if st.session_state["selected_envelope"] == "Insurance" else ""
        st.markdown(f"""
        <div class="metric-card" style="{border_style}">
            <div class="metric-label">🛡️ สำรองประกัน (BAY)</div>
            <div style="font-size: 18px; font-weight: 700;">฿{ins_stat['funded']:,.0f} / 3,500</div>
            <div style="margin-top: 8px;"><span class="badge-pill {badge_cls}">{status_badge}</span></div>
        </div>
        """, unsafe_allow_html=True)
        btn_txt = f"🔍 ดู Txn ({len(ins_txs)})" if not ins_txs.empty else "🔍 ดู Txn (0)"
        if st.button(btn_txt, key="btn_toggle_ins", use_container_width=True):
            st.session_state["selected_envelope"] = None if st.session_state["selected_envelope"] == "Insurance" else "Insurance"
            st.rerun()

    # 4. Rent
    rent_stat = cycle_analytics["fixed_status"]["Rent"]
    with col_env4:
        status_badge = "✅ จ่ายแล้ว" if rent_stat["done"] else "⏳ รอสิ้นเดือน"
        badge_cls = "badge-emerald" if rent_stat["done"] else "badge-amber"
        border_style = "border: 2px solid #2563EB; box-shadow: 0 4px 12px rgba(37,99,235,0.15);" if st.session_state["selected_envelope"] == "Rent" else ""
        st.markdown(f"""
        <div class="metric-card" style="{border_style}">
            <div class="metric-label">🏠 ค่าเช่าห้อง (Rent)</div>
            <div style="font-size: 18px; font-weight: 700;">฿{rent_stat['spent']:,.0f} / 6,000</div>
            <div style="margin-top: 8px;"><span class="badge-pill {badge_cls}">{status_badge}</span></div>
        </div>
        """, unsafe_allow_html=True)
        btn_txt = f"🔍 ดู Txn ({len(rent_txs)})" if not rent_txs.empty else "🔍 ดู Txn (0)"
        if st.button(btn_txt, key="btn_toggle_rent", use_container_width=True):
            st.session_state["selected_envelope"] = None if st.session_state["selected_envelope"] == "Rent" else "Rent"
            st.rerun()

    # 5. Utilities & Phone
    util_stat = cycle_analytics["fixed_status"]["Utilities_Phone"]
    with col_env5:
        status_badge = "✅ จ่ายครบแล้ว" if util_stat["done"] else f"⏳ จ่ายแล้ว ฿{util_stat['spent']:,.0f}"
        badge_cls = "badge-emerald" if util_stat["done"] else "badge-amber"
        border_style = "border: 2px solid #2563EB; box-shadow: 0 4px 12px rgba(37,99,235,0.15);" if st.session_state["selected_envelope"] == "Utilities_Phone" else ""
        st.markdown(f"""
        <div class="metric-card" style="{border_style}">
            <div class="metric-label">⚡ ค่าน้ำ/ไฟ/เน็ต/โทรศัพท์</div>
            <div style="font-size: 18px; font-weight: 700;">฿{util_stat['spent']:,.0f} / {util_stat['budget']:,.0f}</div>
            <div style="margin-top: 8px;"><span class="badge-pill {badge_cls}">{status_badge}</span></div>
        </div>
        """, unsafe_allow_html=True)
        btn_txt = f"🔍 ดู Txn ({len(util_txs)})" if not util_txs.empty else "🔍 ดู Txn (0)"
        if st.button(btn_txt, key="btn_toggle_util", use_container_width=True):
            st.session_state["selected_envelope"] = None if st.session_state["selected_envelope"] == "Utilities_Phone" else "Utilities_Phone"
            st.rerun()

    # Toggleable Envelope Details View Panel
    sel_env = st.session_state.get("selected_envelope")
    if sel_env:
        env_meta_map = {
            "Mom": {"name": "❤️ ให้คุณแม่ (Mom Support)", "budget": 5000.0, "spent": mom_stat["spent"], "txs": mom_txs},
            "DCA": {"name": "📈 DCA ลงทุนรายเดือน", "budget": 4800.0, "spent": dca_stat["spent"], "txs": dca_txs},
            "Insurance": {"name": "🛡️ สำรองกองทุนประกัน (BAY Insurance Fund)", "budget": 3500.0, "spent": ins_stat["funded"], "txs": ins_txs},
            "Rent": {"name": "🏠 ค่าเช่าห้องพัก (Rent Provision)", "budget": 6000.0, "spent": rent_stat["spent"], "txs": rent_txs},
            "Utilities_Phone": {"name": "⚡ ค่าน้ำ / ค่าไฟ / เน็ตบ้าน / โทรศัพท์ (Utilities & Net)", "budget": util_stat["budget"], "spent": util_stat["spent"], "txs": util_txs}
        }
        
        current_env = env_meta_map.get(sel_env)
        if current_env:
            tx_detail_df = current_env["txs"]
            
            st.markdown(f"""
            <div style="background: #F8FAFC; border: 1.5px solid #93C5FD; border-radius: 12px; padding: 14px 18px; margin-top: 14px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 15px; font-weight: 700; color: #1E3A8A;">🔍 รายการธุรกรรม: {current_env['name']}</div>
                        <div style="font-size: 12.5px; color: #64748B; margin-top: 2px;">
                            ยอดตัดจ่ายจริงในงวดนี้: <b style="color: #2563EB;">฿{current_env['spent']:,.2f}</b> / งบเป้าหมาย ฿{current_env['budget']:,.2f}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if not tx_detail_df.empty:
                show_df = tx_detail_df[["Date", "Type", "From_Account", "To_Account", "Amount", "Note", "Transaction_ID"]].copy()
                show_df["Account_Flow"] = [
                    f"{r['From_Account'] or 'Cash'} ➡️ {r['To_Account'] or 'External'}" if r['Type'] == 'Internal_Transfer'
                    else f"{r['From_Account'] or 'Cash'} (ตัดจ่ายตรง)"
                    for _, r in show_df.iterrows()
                ]
                
                renamed_show_df = show_df[["Date", "Account_Flow", "Note", "Amount", "Transaction_ID"]].rename(columns={
                    "Date": "📅 วันที่",
                    "Account_Flow": "🔄 เส้นทางบัญชี",
                    "Note": "📝 บันทึก",
                    "Amount": "💰 ยอดเงิน",
                    "Transaction_ID": "🔑 Tx ID"
                })
                st.dataframe(
                    renamed_show_df,
                    column_config={
                        "📅 วันที่": st.column_config.TextColumn(width="small"),
                        "🔄 เส้นทางบัญชี": st.column_config.TextColumn(width="medium"),
                        "📝 บันทึก": st.column_config.TextColumn(width="large"),
                        "💰 ยอดเงิน": st.column_config.NumberColumn(format="฿%.2f", width="medium"),
                        "🔑 Tx ID": st.column_config.TextColumn(width="small")
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=min(250, 60 + len(show_df) * 40)
                )
            else:
                st.info(f"⏳ ยังไม่มีรายการธุรกรรมที่บันทึกตัดจ่ายสำหรับ '{current_env['name']}' ในงวดปัจจุบัน")
            
            col_close1, col_close2 = st.columns([1, 4])
            with col_close1:
                if st.button("❌ ปิดรายละเอียด", key="btn_close_env_detail", use_container_width=True):
                    st.session_state["selected_envelope"] = None
                    st.rerun()

# =============================================================
# TAB 2: CREDIT CARDS & BILLS (บริหารบิลบัตรเครดิต & ยอดรอจ่าย)
# =============================================================
with tab_pending_cc:
    st.markdown("### 💳 บริหารบิลบัตรเครดิต & ยอดรอจ่าย (Credit Cards & Bills Management)")
    st.caption("ระบบติดตาม 2 มิติ: 1) ยอดตามใบแจ้งยอด & กำหนดวันชำระของบัตรแต่ละใบ  2) รายการรูดบัตรที่รอหาเงินมาโอนเข้า KBANK")

    cc_subtab1, cc_subtab2 = st.tabs([
        "🏛️ 1. ยอดใบแจ้งยอด & วันครบกำหนดชำระ (Statement Bills & Due Dates)",
        "🔄 2. รายการรูดบัตรที่รอโอนเข้า KBANK (Unbacked Swipes)"
    ])

    # ------------------ SUBTAB 1: STATEMENT BILLS ------------------
    with cc_subtab1:
        cc_summary = engine.get_credit_cards_summary()
        ui_components.render_credit_card_kpis(cc_summary)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 📋 รายการบิลบัตรเครดิตตามใบแจ้งยอด (Statement Breakdown)")

        today_day = date.today().day
        today_date = date.today()

        cards = cc_summary["cards"]
        cols_cards = st.columns(len(cards)) if len(cards) <= 3 else None

        for card in cards:
            c_id = card["Card_ID"]
            c_name = card["Card_Name"]
            b_name = card["Bank_Name"]
            due_d = card["Due_Day"]
            stmt_amt = card["Statement_Amount"]
            paid_amt = card["Paid_Amount"]
            rem_amt = card["Remaining_Amount"]
            is_paid = card["Status"] == "Paid" or rem_amt <= 0

            # Due day text & badge
            days_diff = due_d - today_day
            if is_paid:
                due_badge = "badge-emerald"
                due_text = f"✅ ชำระครบแล้ว (ครบกำหนดวันที่ {due_d})"
            elif days_diff == 0:
                due_badge = "badge-rose"
                due_text = f"🚨 ครบกำหนดชำระวันนี้! (วันที่ {due_d})"
            elif days_diff == 1:
                due_badge = "badge-rose"
                due_text = f"⚠️ ครบกำหนดชำระพรุ่งนี้! (วันที่ {due_d})"
            elif 0 < days_diff <= 5:
                due_badge = "badge-amber"
                due_text = f"⏳ เหลืออีก {days_diff} วัน (วันที่ {due_d})"
            else:
                due_badge = "badge-primary"
                due_text = f"🗓️ จ่ายก่อนวันที่ {due_d}"

            card_border = "#059669" if is_paid else ("#DC2626" if days_diff <= 1 else "#2563EB")
            logo_html = ui_components.get_bank_logo_html(c_id, 24)

            with st.container():
                st.markdown(f"""
                <div class="account-card" style="border-left: 4px solid {card_border}; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                        <div>
                            <span style="font-size: 16px; font-weight: 700; color: #0F172A;">{logo_html} {c_name}</span>
                            <span class="badge-pill {due_badge}" style="margin-left: 8px;">{due_text}</span>
                            <div style="font-size: 12.5px; color: #64748B; margin-top: 4px;">
                                ยอดตามใบแจ้งยอด: <b>฿{stmt_amt:,.2f}</b> • ชำระแล้ว: <b style="color: #059669;">฿{paid_amt:,.2f}</b>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 11px; color: #64748B; text-transform: uppercase;">ยอดที่ต้องจ่ายคงเหลือ</div>
                            <div style="font-size: 22px; font-weight: 800; color: {'#059669' if is_paid else '#DC2626'};">
                                ฿{rem_amt:,.2f}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if not is_paid and rem_amt > 0:
                    col_pbtn1, col_pbtn2 = st.columns(2)
                    with col_pbtn1:
                        if st.button(f"⚡ ชำระบิลจาก KBANK (฿{rem_amt:,.2f})", key=f"pay_kbank_{c_id}", use_container_width=True):
                            backend.pay_credit_card(c_id, pay_amount=rem_amt, from_account="KBANK")
                            st.success(f"✅ บันทึกตัดจ่ายบิลบัตร {c_name} ฿{rem_amt:,.2f} จาก KBANK เรียบร้อย!")
                            st.rerun()
                    with col_pbtn2:
                        if st.button(f"⚡ ชำระบิลจาก Thai Credit (฿{rem_amt:,.2f})", key=f"pay_tc_{c_id}", use_container_width=True):
                            backend.pay_credit_card(c_id, pay_amount=rem_amt, from_account="Thai Credit")
                            st.success(f"✅ บันทึกตัดจ่ายบิลบัตร {c_name} ฿{rem_amt:,.2f} จาก Thai Credit เรียบร้อย!")
                            st.rerun()

                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

        with st.expander("✏️ ปรับแก้ / อัปเดตยอดใบแจ้งยอดประจำเดือน (Edit Statement Amounts)"):
            st.caption("อัปเดตยอดบิลตามใบแจ้งหนี้จริงที่ธนาคารส่งมาในแต่ละรอบบิล")
            with st.form("edit_credit_cards_form"):
                cols_form = st.columns(len(cards)) if len(cards) <= 5 else [st.columns(2)]
                new_amounts = {}
                for idx, c in enumerate(cards):
                    c_id = c["Card_ID"]
                    col_target = cols_form[idx] if cols_form and idx < len(cols_form) else st
                    with col_target:
                        new_amounts[c_id] = st.number_input(
                            f"{c['Card_Name']} (ครบกำหนดวันที่ {c['Due_Day']})",
                            min_value=0.0,
                            step=100.0,
                            value=float(c["Statement_Amount"]),
                            format="%.2f",
                            key=f"edit_amt_{c_id}"
                        )
                if st.form_submit_button("💾 บันทึกยอดใบแจ้งยอดใหม่", use_container_width=True):
                    for cid, amt in new_amounts.items():
                        backend.update_credit_card(card_id=cid, statement_amount=amt)
                    st.success("✅ อัปเดตยอดใบแจ้งยอดบัตรเครดิตเรียบร้อย!")
                    st.rerun()

    # ------------------ SUBTAB 2: UNBACKED SWIPES ------------------
    with cc_subtab2:
        pending_summary = engine.get_pending_cc_summary()
        ui_components.render_pending_cc_kpis(pending_summary, summary)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        with st.expander("➕ บันทึกรายการรูดบัตรใหม่ (ที่รอหาเงินมาโอนเข้า KBANK)", expanded=False):
            with st.form("new_pending_cc_form", clear_on_submit=True):
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    p_date = st.date_input("วันที่รูดบัตร (Swipe Date)", value=date.today())
                    p_item = st.text_input("ชื่อรายการ / สินค้าที่รูด", placeholder="เช่น เติมน้ำมัน, ช้อปปิ้งออนไลน์, กินเลี้ยง")
                with col_p2:
                    p_amount = st.number_input("ยอดเงินที่รูด (฿)", min_value=1.0, step=50.0, value=200.0, format="%.2f")
                    p_cat = st.selectbox(
                        "หมวดหมู่งบ:",
                        options=config.CATEGORY_NAMES,
                        format_func=lambda x: config.CATEGORIES[x]["label"]
                    )
                p_note = st.text_input("หมายเหตุเพิ่มเติม (ถ้ามี)", placeholder="เช่น รูดบัตรไว้ก่อน รอเงินเข้ากระเป๋าค่อยโอนเข้า KBANK")
                
                p_submit = st.form_submit_button("💾 บันทึกรายการรอโอน (Add Pending CC)", use_container_width=True)
                if p_submit:
                    if p_item.strip():
                        backend.add_pending_cc(
                            date_val=p_date,
                            item_name=p_item.strip(),
                            category=p_cat,
                            amount=p_amount,
                            note=p_note.strip()
                        )
                        st.success(f"✅ บันทึกรายการ '{p_item.strip()}' ฿{p_amount:,.2f} รอโอนเข้า KBANK เรียบร้อย!")
                        st.rerun()
                    else:
                        st.error("กรุณาระบุชื่อรายการ/สินค้าที่รูด")

        st.markdown("#### 📋 รายการค่าบัตรที่รอหาเงินมาโอนเข้า KBANK")
        
        pending_items = pending_summary["pending_items"]
        if not pending_items:
            st.info("🎉 **ยอดเยี่ยม! ไม่มีรายการค่าบัตรรอโอน** ทุกยอดรูดบัตรได้รับการสำรองเงินเข้า KBANK ครบถ้วนแล้ว (Zero CC Debt 100%)")
        else:
            for idx, item in enumerate(pending_items):
                cat_meta = config.CATEGORIES.get(item["Category"], {"label": item["Category"], "icon": "📦"})
                with st.container():
                    st.markdown(f"""
                    <div class="account-card" style="border-left: 4px solid #DC2626; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                            <div>
                                <span style="font-size: 16px; font-weight: 700; color: #0F172A;">{cat_meta['icon']} {item['Item_Name']}</span>
                                <span class="badge-pill badge-rose" style="margin-left: 8px;">⏳ รอโอนเงินเข้า KBANK</span>
                                <div style="font-size: 12px; color: #64748B; margin-top: 4px;">
                                    📅 รูดเมื่อวันที่: <b>{item['Date']}</b> • หมวดหมู่: <b>{cat_meta['label']}</b>
                                    {f' • หมายเหตุ: <i>{item["Note"]}</i>' if item["Note"] else ''}
                                </div>
                            </div>
                            <div style="font-size: 22px; font-weight: 800; color: #DC2626;">
                                ฿{item['Amount']:,.2f}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
                    with col_btn1:
                        if st.button(f"⚡ โอนเคลียร์จาก SCB ➡️ KBANK (฿{item['Amount']:,.0f})", key=f"clear_scb_{item['Pending_ID']}", use_container_width=True):
                            backend.clear_pending_cc(item["Pending_ID"], from_account="SCB")
                            st.success(f"✅ โอนเงิน ฿{item['Amount']:,.2f} จาก SCB ➡️ KBANK เพื่อเคลียร์รายการ '{item['Item_Name']}' เรียบร้อย!")
                            st.rerun()
                    with col_btn2:
                        if st.button(f"⚡ โอนเคลียร์จาก Thai Credit ➡️ KBANK (฿{item['Amount']:,.0f})", key=f"clear_tc_{item['Pending_ID']}", use_container_width=True):
                            backend.clear_pending_cc(item["Pending_ID"], from_account="Thai Credit")
                            st.success(f"✅ โอนเงิน ฿{item['Amount']:,.2f} จาก Thai Credit ➡️ KBANK เพื่อเคลียร์รายการ '{item['Item_Name']}' เรียบร้อย!")
                            st.rerun()
                    with col_btn3:
                        if st.button("🗑️ ลบ", key=f"del_pcc_{item['Pending_ID']}", use_container_width=True):
                            backend.delete_pending_cc(item["Pending_ID"])
                            st.warning("ลบรายการเรียบร้อย")
                            st.rerun()
                    
                    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

        # Cleared History
        cleared_items = pending_summary["cleared_items"]
        if cleared_items:
            with st.expander(f"📜 ประวัติรายการที่โอนเคลียร์เข้า KBANK แล้ว ({len(cleared_items)} รายการ)"):
                cleared_df = pd.DataFrame(cleared_items)[["Date", "Item_Name", "Category", "Amount", "Cleared_From_Account", "Cleared_At", "Note"]]
                cleared_df.columns = ["📅 วันที่รูด", "🛍️ รายการ", "📂 หมวดหมู่", "💰 ยอดเงิน", "🏦 บัญชีที่โอนเคลียร์", "⏰ เวลาที่เคลียร์", "📝 หมายเหตุ"]
                st.dataframe(
                    cleared_df,
                    column_config={
                        "📅 วันที่รูด": st.column_config.TextColumn(width="small"),
                        "🛍️ รายการ": st.column_config.TextColumn(width="medium"),
                        "📂 หมวดหมู่": st.column_config.TextColumn(width="small"),
                        "💰 ยอดเงิน": st.column_config.NumberColumn(format="฿%.2f", width="medium"),
                        "🏦 บัญชีที่โอนเคลียร์": st.column_config.TextColumn(width="small"),
                        "⏰ เวลาที่เคลียร์": st.column_config.TextColumn(width="medium"),
                        "📝 หมายเหตุ": st.column_config.TextColumn(width="large")
                    },
                    hide_index=True,
                    use_container_width=True
                )


st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# =============================================================
# TAB 3: ACCOUNT LEDGERS & STATEMENTS
# =============================================================
with tab_ledgers:
    st.markdown("### 🏦 สมุดบัญชีและสเตทเมนต์รายบัญชี (Account Statements & Ledger)")
    
    selected_account = st.selectbox(
        "เลือกบัญชีที่ต้องการตรวจสอบสเตทเมนต์:",
        options=config.ACCOUNT_NAMES,
        format_func=lambda x: f"{config.ACCOUNTS[x]['icon']} {config.ACCOUNTS[x]['name']} (คงเหลือ ฿{summary['accounts'][x]['current_balance']:,.2f})"
    )

    acc_meta = config.ACCOUNTS[selected_account]
    logo_html = ui_components.get_bank_logo_html(selected_account, size=28)
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin: 10px 0 16px 0; padding: 12px 18px; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
        {logo_html}
        <div>
            <div style="font-size:16px; font-weight:700; color:#0F172A;">{acc_meta['name']}</div>
            <div style="font-size:12px; color:#64748B;">{acc_meta['role']} • ยอดคงเหลือปัจจุบัน: <b style="color:#2563EB;">฿{summary['accounts'][selected_account]['current_balance']:,.2f}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    statement_df = engine.get_account_statement(selected_account)
    
    if not statement_df.empty:
        # Running Balance Chart
        chart_data = statement_df.copy()
        
        # Build clean hover labels & step sequence
        hover_texts = []
        x_labels = []
        for idx_step, r in chart_data.iterrows():
            d_str = str(r["Date"])
            desc = r["Description"]
            bal_val = float(r["Balance"])
            in_val = float(r["Inflow"])
            out_val = float(r["Outflow"])
            
            in_text = f"<br>🟢 เงินเข้า: +฿{in_val:,.2f}" if in_val > 0 else ""
            out_text = f"<br>🔴 เงินออก: -฿{out_val:,.2f}" if out_val > 0 else ""
            hover_texts.append(f"<b>{desc}</b><br>📅 วันที่: {d_str}{in_text}{out_text}<br>💰 <b>คงเหลือ: ฿{bal_val:,.2f}</b>")
            
            if len(chart_data) <= 1:
                x_labels.append(d_str)
            else:
                x_labels.append(f"{d_str} (#{idx_step + 1})")

        fig_bal = go.Figure()
        fig_bal.add_trace(go.Scatter(
            x=x_labels,
            y=chart_data["Balance"],
            mode="lines+markers",
            name=f"ยอดคงเหลือ {selected_account}",
            line=dict(color=config.ACCOUNTS[selected_account]["color"], width=2.5),
            marker=dict(size=7, color=config.ACCOUNTS[selected_account]["color"]),
            hovertext=hover_texts,
            hoverinfo="text",
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.05)"
        ))
        fig_bal.update_layout(
            title=f"📊 เส้นทางยอดเงินคงเหลือ (Running Balance) - {selected_account}",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=dict(color="#334155", family="Prompt, Inter", size=12),
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(
                type="category",
                title="ลำดับรายการ / วันที่ (Transaction Sequence & Date)",
                gridcolor="#F1F5F9",
                linecolor="#E2E8F0"
            ),
            yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="ยอดคงเหลือ (THB)"),
            height=280
        )
        st.plotly_chart(fig_bal, use_container_width=True, config={"displayModeBar": False})

        # Statement Table
        st.markdown("##### 📜 รายการเดินบัญชี (Statement Records)")
        
        display_df = statement_df[["Date", "Type", "Description", "Inflow", "Outflow", "Balance", "Note", "Transaction_ID"]].copy()
        display_df["Inflow"] = display_df["Inflow"].apply(lambda x: float(x) if float(x) > 0 else None)
        display_df["Outflow"] = display_df["Outflow"].apply(lambda x: float(x) if float(x) > 0 else None)
        display_df.columns = ["วันที่", "ประเภท", "รายการ / หมวดหมู่", "เงินเข้า (+)", "เงินออก (-)", "ยอดคงเหลือ", "บันทึกช่วยจำ", "Tx ID"]
        
        st.dataframe(
            display_df,
            column_config={
                "วันที่": st.column_config.TextColumn("📅 วันที่", width="small"),
                "ประเภท": st.column_config.TextColumn("🏷️ ประเภท", width="small"),
                "รายการ / หมวดหมู่": st.column_config.TextColumn("📂 รายการ / หมวดหมู่", width="medium"),
                "เงินเข้า (+)": st.column_config.NumberColumn("📥 เงินเข้า (+)", format="฿%.2f", width="medium"),
                "เงินออก (-)": st.column_config.NumberColumn("📤 เงินออก (-)", format="฿%.2f", width="medium"),
                "ยอดคงเหลือ": st.column_config.NumberColumn("💰 ยอดคงเหลือ", format="฿%.2f", width="medium"),
                "บันทึกช่วยจำ": st.column_config.TextColumn("📝 บันทึกช่วยจำ", width="large"),
                "Tx ID": st.column_config.TextColumn("🔑 Tx ID", width="small")
            },
            hide_index=True,
            use_container_width=True,
            height=450
        )
        
        # Delete Transaction Option
        with st.expander("🗑️ ลบ / ยกเลิกรายการที่บันทึกผิด (Delete / Undo Transaction)", expanded=False):
            all_tx_list = backend.get_transactions()
            if all_tx_list:
                st.caption("เลือกลบรายการที่กดซ้ำหรือบันทึกผิดพลาด ระบบจะคำนวณยอดเงินคงเหลือของทุกบัญชีใหม่อัตโนมัติ")
                tx_dict = {t["Transaction_ID"]: t for t in all_tx_list}
                
                selected_del = st.selectbox(
                    "เลือกรายการที่ต้องการลบ:",
                    options=list(tx_dict.keys()),
                    format_func=lambda tid: (
                        f"📅 {tx_dict[tid]['Date']} | {tx_dict[tid]['Type']} | "
                        f"{config.CATEGORIES.get(tx_dict[tid]['Category'], {}).get('label', tx_dict[tid]['Category'])} | "
                        f"฿{tx_dict[tid]['Amount']:,.2f} "
                        f"({tx_dict[tid]['From_Account'] or 'None'} ➡️ {tx_dict[tid]['To_Account'] or 'External'})"
                        f"{' — ' + tx_dict[tid]['Note'] if tx_dict[tid]['Note'] else ''}"
                    )
                )
                
                col_del_btn1, col_del_btn2 = st.columns([1, 3])
                with col_del_btn1:
                    if st.button("🗑️ ยืนยันการลบรายการนี้", type="primary", use_container_width=True):
                        target_info = tx_dict[selected_del]
                        if backend.delete_transaction(selected_del):
                            st.success(f"✅ ลบรายการ '{target_info.get('Note') or target_info.get('Category')}' ฿{target_info['Amount']:,.2f} เรียบร้อยแล้ว!")
                            st.rerun()
            else:
                st.info("ไม่มีรายการธุรกรรมในระบบให้ลบ (ยกเว้นยอดเงินเริ่มต้น)")
    else:
        st.info(f"ยังไม่มีรายการเคลื่อนไหวสำหรับบัญชี {selected_account}")

# =============================================================
# TAB 3: WISHLIST TRACKER
# =============================================================
with tab_wishlist:
    st.markdown("### 🎁 เป้าหมายของรางวัลและไลฟ์สไตล์ (Wishlist Tracker)")
    st.caption("วางแผนซื้อของรางวัลชีวิตโดยไม่กระทบงบหลัก พร้อมบันทึกการตัดจ่ายเมื่อซื้อสำเร็จ")

    wishlist_items = backend.get_wishlist()
    
    # Wishlist KPI Summary Cards
    total_wish_target = sum(float(i.get("Target_Price", 0)) for i in wishlist_items)
    total_wish_saved = sum(float(i.get("Current_Saved", 0)) for i in wishlist_items)
    purchased_count = sum(1 for i in wishlist_items if i.get("Status") == "Purchased")
    pending_count = len(wishlist_items) - purchased_count

    w_col1, w_col2, w_col3, w_col4 = st.columns(4)
    with w_col1:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #7C3AED;">
            <div class="metric-label">🎁 มูลค่าเป้าหมายรวม</div>
            <div class="metric-value">฿{total_wish_target:,.2f}</div>
            <div class="metric-sub neutral">ทั้งหมด {len(wishlist_items)} รายการ</div>
        </div>
        """, unsafe_allow_html=True)
    with w_col2:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #059669;">
            <div class="metric-label">💰 เงินสะสมในเป้าหมาย</div>
            <div class="metric-value" style="color: #059669;">฿{total_wish_saved:,.2f}</div>
            <div class="metric-sub neutral">ความคืบหน้าภาพรวม {int((total_wish_saved/total_wish_target)*100) if total_wish_target > 0 else 0}%</div>
        </div>
        """, unsafe_allow_html=True)
    with w_col3:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #2563EB;">
            <div class="metric-label">⏳ กำลังสะสม / รอซื้อ</div>
            <div class="metric-value" style="color: #2563EB;">{pending_count} <span style="font-size: 15px; color: #64748B;">รายการ</span></div>
            <div class="metric-sub neutral">เป้าหมายที่อยู่ระหว่างดำเนินการ</div>
        </div>
        """, unsafe_allow_html=True)
    with w_col4:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #10B981;">
            <div class="metric-label">🎉 พิชิตเป้าหมายแล้ว</div>
            <div class="metric-value" style="color: #10B981;">{purchased_count} <span style="font-size: 15px; color: #64748B;">รายการ</span></div>
            <div class="metric-sub neutral">ซื้อสำเร็จเรียบร้อย</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    col_w1, col_w2 = st.columns([3, 2])
    
    with col_w1:
        st.markdown("#### 🛍️ รายการของที่อยากได้ (Wishlist Items)")
        
        if not wishlist_items:
            st.info("ยังไม่มีเป้าหมายใน Wishlist เพิ่มเป้าหมายใหม่ได้ที่ฟอร์มด้านขวา")
        else:
            for idx, item in enumerate(wishlist_items):
                target_price = float(item.get("Target_Price", 0.0))
                saved_amt = float(item.get("Current_Saved", 0.0))
                status = item.get("Status", "Pending")
                priority = item.get("Priority", "Medium")
                pct = min(100, int((saved_amt / target_price) * 100)) if target_price > 0 else 0
                
                is_purchased = status == "Purchased"
                card_border = "#059669" if is_purchased else ("#7C3AED" if priority == "High" else "#2563EB")
                
                with st.container():
                    st.markdown(f"""
                    <div class="account-card" style="border-left: 4px solid {card_border}; margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                            <div>
                                <span style="font-size: 16px; font-weight: 700; color: #0F172A;">🎁 {item['Item_Name']}</span>
                                <span class="badge-pill {'badge-emerald' if is_purchased else ('badge-rose' if priority == 'High' else 'badge-primary')}" style="margin-left: 6px;">
                                    {'✅ ซื้อแล้ว' if is_purchased else f'⚡ {priority} Priority'}
                                </span>
                                <div style="font-size: 12.5px; color: #64748B; margin-top: 4px;">
                                    📅 เดือนเป้าหมาย: <b>{item.get('Target_Month', '2026-08')}</b> • สถานะ: <b>{status}</b>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 11px; color: #64748B; text-transform: uppercase;">ราคาเป้าหมาย</div>
                                <div style="font-size: 20px; font-weight: 800; color: {'#059669' if is_purchased else '#2563EB'};">
                                    ฿{target_price:,.2f}
                                </div>
                                <div style="font-size: 12px; color: #64748B;">
                                    สะสมแล้ว: <b>฿{saved_amt:,.0f}</b> ({pct}%)
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.progress(pct / 100)
                    
                    # Action Buttons for Wishlist Item
                    if not is_purchased:
                        col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])
                        with col_btn1:
                            if st.button(f"⚡ ซื้อแล้ว (ตัดจาก SCB ฿{target_price:,.0f})", key=f"buy_wish_scb_{idx}", use_container_width=True):
                                backend.add_transaction(
                                    date_val=date.today(),
                                    tx_type="Expense",
                                    from_account="SCB",
                                    to_account=None,
                                    category="Wishlist_Hobby",
                                    amount=target_price,
                                    note=f"🎁 ซื้อของรางวัลชีวิต: {item['Item_Name']}"
                                )
                                wishlist_items[idx]["Status"] = "Purchased"
                                wishlist_items[idx]["Current_Saved"] = target_price
                                backend.save_wishlist(wishlist_items)
                                st.success(f"🎉 บันทึกการซื้อ '{item['Item_Name']}' ฿{target_price:,.2f} ตัดจาก SCB เรียบร้อย!")
                                st.rerun()
                        with col_btn2:
                            if st.button(f"⚡ ซื้อแล้ว (ตัดจาก Thai Credit ฿{target_price:,.0f})", key=f"buy_wish_tc_{idx}", use_container_width=True):
                                backend.add_transaction(
                                    date_val=date.today(),
                                    tx_type="Expense",
                                    from_account="Thai Credit",
                                    to_account=None,
                                    category="Wishlist_Hobby",
                                    amount=target_price,
                                    note=f"🎁 ซื้อของรางวัลชีวิต: {item['Item_Name']}"
                                )
                                wishlist_items[idx]["Status"] = "Purchased"
                                wishlist_items[idx]["Current_Saved"] = target_price
                                backend.save_wishlist(wishlist_items)
                                st.success(f"🎉 บันทึกการซื้อ '{item['Item_Name']}' ฿{target_price:,.2f} ตัดจาก Thai Credit เรียบร้อย!")
                                st.rerun()
                        with col_btn3:
                            if st.button("🗑️ ลบ", key=f"del_wish_{idx}", use_container_width=True):
                                wishlist_items.pop(idx)
                                backend.save_wishlist(wishlist_items)
                                st.warning("ลบรายการออกจาก Wishlist เรียบร้อย")
                                st.rerun()
                    else:
                        col_p1, col_p2 = st.columns([4, 1])
                        with col_p1:
                            st.caption("✅ รายการนี้ซื้อสำเร็จและบันทึกตัดบัญชีเรียบร้อยแล้ว")
                        with col_p2:
                            if st.button("🗑️ ลบ", key=f"del_wish_done_{idx}", use_container_width=True):
                                wishlist_items.pop(idx)
                                backend.save_wishlist(wishlist_items)
                                st.warning("ลบรายการออกจาก Wishlist เรียบร้อย")
                                st.rerun()

                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    with col_w2:
        st.markdown("#### ➕ เพิ่มเป้าหมาย Wishlist ใหม่")
        with st.form("new_wishlist_item_form", clear_on_submit=True):
            new_item_name = st.text_input("ชื่อสิ่งของ / รางวัล", placeholder="เช่น น้ำหอม, หูฟังไร้สาย, รองเท้าผ้าใบ")
            new_price = st.number_input("ราคาเป้าหมาย (THB)", min_value=100.0, step=100.0, value=2700.0, format="%.2f")
            new_month = st.text_input("เดือนเป้าหมาย (Target Month)", value=date.today().strftime("%Y-%m"))
            new_priority = st.selectbox("ลำดับความสำคัญ (Priority)", options=["High", "Medium", "Low"], index=0)
            new_saved = st.number_input("เงินที่เก็บสะสมไว้แล้ว (THB)", min_value=0.0, step=100.0, value=0.0, format="%.2f")
            
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
                value=acc_initials.get("SCB", 3450.0),
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

    with st.expander("🧹 จัดการล้างประวัติทั้งหมด & เริ่มต้นใหม่ (Reset All Data)"):
        st.caption("ล้างรายการธุรกรรมและรายการค่าบัตรรอโอนทั้งหมดออก เพื่อเริ่มบันทึกใหม่จากยอดเงินเริ่มต้นปัจจุบัน")
        if st.button("🗑️ ล้างรายการทั้งหมดและเริ่มใหม่ (Reset All Transactions & Pending CC)", type="secondary"):
            backend.reset_all_data()
            st.success("✅ ล้างรายการธุรกรรมและค่าบัตรรอโอนทั้งหมดเรียบร้อย! ยอดคงเหลือกลับมาเท่ากับยอดเริ่มต้นพอดี")
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
