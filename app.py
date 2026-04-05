import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & EXECUTIVE DARK THEME ---
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

# --- 2. DATA ENGINE (CORE STABILITY) ---
def load_data(file_name, columns):
    if os.path.exists(file_name):
        return pd.read_csv(file_name)
    return pd.DataFrame(columns=columns)

# Initialize Session States
if 'accounts' not in st.session_state:
    if os.path.exists("aura_accounts.csv"):
        st.session_state.accounts = pd.read_csv("aura_accounts.csv").iloc[0].to_dict()
    else:
        st.session_state.accounts = {"Checking": 8450.0, "Savings": 25000.0, "Retirement": 142000.0}

if 'debt' not in st.session_state:
    st.session_state.debt = load_data("aura_debt.csv", ["Name", "Balance"])

if 'expenses' not in st.session_state:
    st.session_state.expenses = load_data("aura_expenses.csv", ["Date", "Category", "Amount"])

# --- 3. DASHBOARD HELPERS ---
def draw_hero(col, label, value, color="#FFFFFF"):
    html = f"""
    <div class="hero-card">
        <div class="hero-label">{label}</div>
        <div class="hero-val" style="color:{color}">${value:,.0f}</div>
    </div>
    """
    col.markdown(html, unsafe_allow_html=True)

# --- 4. MAIN NAVIGATION ---
with st.sidebar:
    st.title("🏛️ AURA")
    page = st.radio("MENU", ["Dashboard", "Debt Portfolio", "Weekly Budget", "Monthly Budget"])
    st.markdown("---")
    if st.button("Hard Reset All Data"):
        for f in ["aura_accounts.csv", "aura_debt.csv", "aura_expenses.csv"]:
            if os.path.exists(f): os.remove(f)
        st.rerun()

# --- 5. PAGE: DASHBOARD ---
if page == "Dashboard":
    st.title("Executive Dashboard")

    # Math Logic
    total_debt = st.session_state.debt['Balance'].sum() if not st.session_state.debt.empty else 0
    total_assets = sum(st.session_state.accounts.values())
    net_worth = total_assets - total_debt

    # HERO ROW
    h1, h2, h3, h4, h5 = st.columns(5)
    draw_hero(h1, "Net Worth", net_worth, color="#D4AF37")
    draw_hero(h2, "Checking", st.session_state.accounts['Checking'])
    draw_hero(h3, "Savings", st.session_state.accounts['Savings'])
    draw_hero(h4, "Retirement", st.session_state.accounts['Retirement'])
    draw_hero(h5, "Total Debt", total_debt, color="#FF5252")

    st.markdown("<br>", unsafe_allow_html=True)

    # ADJUSTMENT AREA
    with st.expander("🛠️ EDIT ACCOUNT BALANCES", expanded=False):
        c1, c2, c3, c4 = st.columns([1,1,1,1])
        new_ch = c1.number_input("Checking", value=float(st.session_state.accounts['Checking']))
        new_sa = c2.number_input("Savings", value=float(st.session_state.accounts['Savings']))
        new_re = c3.number_input("Retirement", value=float(st.session_state.accounts['Retirement']))
        if c4.button("Save Balances", use_container_width=True):
            st.session_state.accounts = {"Checking": new_ch, "Savings": new_sa, "Retirement": new_re}
            pd.DataFrame([st.session_state.accounts]).to_csv("aura_accounts.csv", index=False)
            st.rerun()

    st.markdown("---")
    
    # PINNED ESSENTIALS
    st.markdown("### 🏛️ Pinned Essentials")
    p_cols = st.columns(3)
    pinned = [{"name": "Rent", "lim": 2400}, {"name": "Groceries", "lim": 600}, {"name": "Savings Goal", "lim": 1000}]
    
    for idx, item in enumerate(pinned):
        spent = st.session_state.expenses[st.session_state.expenses['Category'] == item['name']]['Amount'].sum() if not st.session_state.expenses.empty else 0
        with p_cols[idx]:
            st.markdown(f"""
            <div class="budget-card">
                <div style="font-size:10px; color:#8E8E93; text-transform:uppercase;">{item["name"]}</div>
                <div style="font-size:20px; font-weight:700;">${spent:,.0f} / ${item["lim"]:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(spent/item['lim'], 1.0) if item['lim'] > 0 else 0)

# --- 6. PAGE: DEBT PORTFOLIO ---
elif page == "Debt Portfolio":
    st.title("Debt Portfolio")
    with st.form("add_debt"):
        d_name = st.text_input("Lender Name (e.g., Chase, Auto Loan)")
        d_amt = st.number_input("Current Balance", min_value=0.0)
        if st.form_submit_button("Add Debt Entry"):
            new_row = pd.DataFrame([[d_name, d_amt]], columns=["Name", "Balance"])
            st.session_state.debt = pd.concat([st.session_state.debt, new_row], ignore_index=True)
            st.session_state.debt.to_csv("aura_debt.csv", index=False)
            st.rerun()

    for i, row in st.session_state.debt.iterrows():
        st.markdown(f'<div class="budget-card"><b>{row["Name"]}</b>: ${row["Balance"]:,.0f}</div>', unsafe_allow_html=True)
        if st.button(f"Remove {row['Name']}", key=f"del_{i}"):
            st.session_state.debt = st.session_state.debt.drop(i)
            st.session_state.debt.to_csv("aura_debt.csv", index=False)
            st.rerun()

# --- 7. PAGE: BUDGETS ---
elif page in ["Weekly Budget", "Monthly Budget"]:
    st.title(f"{page} Management")
    st.info("Log your daily spending here to update the Dashboard Essentials.")
    with st.form("log_exp"):
        cat = st.selectbox("Category", ["Rent", "Groceries", "Savings Goal", "Entertainment", "Other"])
        amt = st.number_input("Amount Spent", min_value=0.0)
        if st.form_submit_button("Log Transaction"):
            new_exp = pd.DataFrame([[datetime.now(), cat, amt]], columns=["Date", "Category", "Amount"])
            st.session_state.expenses = pd.concat([st.session_state.expenses, new_exp], ignore_index=True)
            st.session_state.expenses.to_csv("aura_expenses.csv", index=False)
            st.success("Logged!")
            st.rerun()
