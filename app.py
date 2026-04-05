import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. GLOBAL CONFIG ---
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

# --- 2. LIVE DATA ENGINE ---
def load_or_create(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    df = pd.DataFrame(columns=columns)
    df.to_csv(file, index=False)
    return df

# Initialize all data into Session State for Live Updates
if 'accounts' not in st.session_state:
    if os.path.exists("aura_accounts.csv"):
        st.session_state.accounts = pd.read_csv("aura_accounts.csv").iloc[0].to_dict()
    else:
        st.session_state.accounts = {"Checking": 8450.0, "Savings": 25000.0, "Retirement": 142000.0}

if 'debt_df' not in st.session_state:
    st.session_state.debt_df = load_or_create("aura_debt.csv", ["Name", "Balance"])

if 'exp_df' not in st.session_state:
    st.session_state.exp_df = load_or_create("aura_expenses.csv", ["Date", "Category", "Amount"])

# --- 3. THE "CALCULATOR" (Calculates everything live) ---
total_debt = float(st.session_state.debt_df['Balance'].sum()) if not st.session_state.debt_df.empty else 0.0
total_assets = sum(st.session_state.accounts.values())
net_worth = total_assets - total_debt

# --- 4. NAVIGATION ---
with st.sidebar:
    st.title("🏛️ AURA")
    page = st.radio("MENU", ["Dashboard", "Debt Portfolio", "Weekly Budget", "Monthly Budget"])

# --- 5. PAGE: DASHBOARD ---
if page == "Dashboard":
    st.title("Executive Dashboard")

    # HERO ROW (Live Metrics)
    h1, h2, h3, h4, h5 = st.columns(5)
    
    # Helper to draw cards
    def draw(col, lab, val, clr="#FFFFFF"):
        col.markdown(f'<div class="hero-card"><div class="hero-label">{lab}</div><div class="hero-val" style="color:{clr}">${val:,.0f}</div></div>', unsafe_allow_html=True)

    draw(h1, "Net Worth", net_worth, "#D4AF37")
    draw(h2, "Checking", st.session_state.accounts['Checking'])
    draw(h3, "Savings", st.session_state.accounts['Savings'])
    draw(h4, "Retirement", st.session_state.accounts['Retirement'])
    draw(h5, "Total Debt", total_debt, "#FF5252")

    st.markdown("<br>", unsafe_allow_html=True)

    # LIVE ADJUSTMENT
    with st.expander("🛠️ QUICK UPDATE BALANCES", expanded=False):
        c1, c2, c3, c4 = st.columns([1,1,1,1])
        u_ch = c1.number_input("Checking", value=float(st.session_state.accounts['Checking']))
        u_sa = c2.number_input("Savings", value=float(st.session_state.accounts['Savings']))
        u_re = c3.number_input("Retirement", value=float(st.session_state.accounts['Retirement']))
        if c4.button("Update Live", use_container_width=True):
            st.session_state.accounts = {"Checking": u_ch, "Savings": u_sa, "Retirement": u_re}
            pd.DataFrame([st.session_state.accounts]).to_csv("aura_accounts.csv", index=False)
            st.rerun() # Forces immediate calculation refresh

    st.markdown("---")
    st.markdown("### 🏛️ Pinned Essentials")
    
    # Dashboard Progress Sync
    pinned = [{"name": "Rent", "lim": 2400}, {"name": "Groceries", "lim": 600}, {"name": "Savings Goal", "lim": 1000}]
    p_cols = st.columns(3)
    
    for idx, item in enumerate(pinned):
        # Calculate spent amount live from the expense dataframe
        spent = st.session_state.exp_df[st.session_state.exp_df['Category'] == item['name']]['Amount'].sum() if not st.session_state.exp_df.empty else 0
        with p_cols[idx]:
            st.markdown(f'<div class="budget-card"><div class="hero-label">{item["name"]}</div><div class="hero-val">${spent:,.0f} / {item["lim"]}</div></div>', unsafe_allow_html=True)
            st.progress(min(spent/item['lim'], 1.0) if item['lim'] > 0 else 0.0)

# --- 6. PAGE: DEBT PORTFOLIO ---
elif page == "Debt Portfolio":
    st.title("Debt Portfolio")
    with st.form("debt_form", clear_on_submit=True):
        d_n = st.text_input("Lender")
        d_b = st.number_input("Balance", min_value=0.0)
        if st.form_submit_button("Add Debt"):
            new_d = pd.DataFrame([[d_n, d_b]], columns=["Name", "Balance"])
            st.session_state.debt_df = pd.concat([st.session_state.debt_df, new_d], ignore_index=True)
            st.session_state.debt_df.to_csv("aura_debt.csv", index=False)
            st.rerun() # Immediately updates Net Worth on Dashboard

    for i, r in st.session_state.debt_df.iterrows():
        st.markdown(f'<div class="budget-card"><b>{r["Name"]}</b>: ${r["Balance"]:,.0f}</div>', unsafe_allow_html=True)
        if st.button("Delete", key=f"del_{i}"):
            st.session_state.debt_df = st.session_state.debt_df.drop(i)
            st.session_state.debt_df.to_csv("aura_debt.csv", index=False)
            st.rerun()

# --- 7. PAGE: BUDGETS ---
elif page in ["Weekly Budget", "Monthly Budget"]:
    st.title(f"{page} Management")
    with st.form("exp_form", clear_on_submit=True):
        cat = st.selectbox("Category", ["Rent", "Groceries", "Savings Goal", "Other"])
        amt = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Log Spending"):
            new_e = pd.DataFrame([[datetime.now(), cat, amt]], columns=["Date", "Category", "Amount"])
            st.session_state.exp_df = pd.concat([st.session_state.exp_df, new_e], ignore_index=True)
            st.session_state.exp_df.to_csv("aura_expenses.csv", index=False)
            st.rerun() # Immediately updates Budget Bars on Dashboard
