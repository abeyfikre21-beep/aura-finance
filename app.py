import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #02060E; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #D4AF37; }
    .hero-card {
        background: #0D1526; padding: 20px 10px; border-radius: 15px;
        border: 1px solid #1C2C4E; text-align: center; min-height: 110px;
    }
    .hero-label { font-size: 11px; color: #8E8E93; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; font-weight: 600;}
    .hero-val { font-size: 24px; font-weight: 800; color: #FFFFFF; }
    .budget-card {
        background: #0D1526; padding: 18px; border-radius: 12px;
        border: 1px solid #1C2C4E; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE: DATA INITIALIZATION ---
def init_state():
    if 'acct_data' not in st.session_state:
        if os.path.exists("aura_accounts.csv"):
            st.session_state.acct_data = pd.read_csv("aura_accounts.csv").iloc[0].to_dict()
        else:
            st.session_state.acct_data = {"Checking": 0.0, "Savings": 0.0, "Retirement": 0.0}

    if 'debt_df' not in st.session_state:
        st.session_state.debt_df = pd.read_csv("aura_debt.csv") if os.path.exists("aura_debt.csv") else pd.DataFrame(columns=["Name", "Balance"])

    if 'exp_df' not in st.session_state:
        st.session_state.exp_df = pd.read_csv("aura_expenses.csv") if os.path.exists("aura_expenses.csv") else pd.DataFrame(columns=["Date", "Category", "Amount"])

init_state()

# --- 3. MATH ---
d_total = float(st.session_state.debt_df['Balance'].sum()) if not st.session_state.debt_df.empty else 0.0
a_total = sum(st.session_state.acct_data.values())
current_nw = a_total - d_total

# --- 4. SIDE NAVIGATION ---
with st.sidebar:
    st.title("🏛️ AURA")
    st.subheader("MAIN")
    page = st.radio("Navigation", ["Dashboard", "Wealth Tracking", "Weekly Budget", "Monthly Budget"])
    
    st.markdown("---")
    st.subheader("ANALYTICS")
    page_analytics = st.radio("Insights", ["Insights & History"])
    
    st.markdown("---")
    st.subheader("SYSTEM")
    page_system = st.radio("Settings", ["Assistant", "Profile", "App Appearance"])

# --- 5. PAGE: DASHBOARD ---
if page == "Dashboard":
    st.title("Financial Command Center")
    h1, h2, h3, h4, h5 = st.columns(5)
    
    def draw_c(col, l, v, c="#FFFFFF"):
        col.markdown(f'<div class="hero-card"><div class="hero-label">{l}</div><div class="hero-val" style="color:{c}">${v:,.0f}</div></div>', unsafe_allow_html=True)

    draw_c(h1, "Net Worth", current_nw, "#D4AF37")
    draw_c(h2, "Checking Account", st.session_state.acct_data['Checking'])
    draw_c(h3, "Savings", st.session_state.acct_data['Savings'])
    draw_c(h4, "Retirement Fund", st.session_state.acct_data['Retirement'])
    draw_c(h5, "Total Debt", d_total, "#FF5252")

    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.expander("🛠️ QUICK ADJUST HERO NUMBERS"):
        with st.form("hero_edit"):
            c1, c2, c3 = st.columns(3)
            nc = c1.number_input("Checking", value=float(st.session_state.acct_data['Checking']))
            ns = c2.number_input("Savings", value=float(st.session_state.acct_data['Savings']))
            nr = c3.number_input("Retirement", value=float(st.session_state.acct_data['Retirement']))
            if st.form_submit_button("Update Dashboard"):
                st.session_state.acct_data = {"Checking": nc, "Savings": ns, "Retirement": nr}
                pd.DataFrame([st.session_state.acct_data]).to_csv("aura_accounts.csv", index=False)
                st.rerun()

# --- 6. PAGE: WEALTH TRACKING (ASSETS & DEBT) ---
elif page == "Wealth Tracking":
    st.title("Wealth Portfolio")
    col_a, col_d = st.columns(2)
    
    with col_a:
        st.subheader("🏦 Asset Management")
        st.info("Update your primary balances in the Dashboard 'Quick Adjust' menu.")
        st.metric("Total Liquid Assets", f"${a_total:,.2f}")

    with col_d:
        st.subheader("💳 Debt Management")
        with st.form("debt_add", clear_on_submit=True):
            dn = st.text_input("Lender Name")
            db = st.number_input("Current Balance", min_value=0.0)
            if st.form_submit_button("Add Debt"):
                new_d = pd.DataFrame([[dn, db]], columns=["Name", "Balance"])
                st.session_state.debt_df = pd.concat([st.session_state.debt_df, new_row], ignore_index=True)
                st.session_state.debt_df.to_csv("aura_debt.csv", index=False)
                st.rerun()

# --- 7. ANALYTICS & SYSTEM PLACEHOLDERS ---
elif page_analytics == "Insights & History":
    st.title("📊 Insights & History")
    if not st.session_state.exp_df.empty:
        st.dataframe(st.session_state.exp_df, use_container_width=True)
    else:
        st.write("No transaction history found.")

elif page_system == "Assistant":
    st.title("🤖 Aura AI Assistant")
    st.write("How can I help you optimize your wealth today?")

elif page_system == "App Appearance":
    st.title("🎨 App Appearance")
    st.color_picker("Accent Color", "#D4AF37")
