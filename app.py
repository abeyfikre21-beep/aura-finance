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

# --- 2. ENGINE: STATE INITIALIZATION ---
if 'acct_data' not in st.session_state:
    if os.path.exists("aura_accounts.csv"):
        st.session_state.acct_data = pd.read_csv("aura_accounts.csv").iloc[0].to_dict()
    else:
        st.session_state.acct_data = {"Checking": 8450.0, "Savings": 25000.0, "Retirement": 142000.0}

if 'debt_df' not in st.session_state:
    if os.path.exists("aura_debt.csv"): st.session_state.debt_df = pd.read_csv("aura_debt.csv")
    else: st.session_state.debt_df = pd.DataFrame(columns=["Name", "Balance"])

if 'exp_df' not in st.session_state:
    if os.path.exists("aura_expenses.csv"): st.session_state.exp_df = pd.read_csv("aura_expenses.csv")
    else: st.session_state.exp_df = pd.DataFrame(columns=["Date", "Category", "Amount"])

# --- 3. MATH CALCULATIONS ---
d_total = float(st.session_state.debt_df['Balance'].sum()) if not st.session_state.debt_df.empty else 0.0
a_total = sum(st.session_state.acct_data.values())
current_nw = a_total - d_total

# --- 4. NAVIGATION ---
with st.sidebar:
    st.title("🏛️ AURA")
    page = st.radio("MENU", ["Dashboard", "Debt Portfolio", "Weekly Budget", "Monthly Budget"])

# --- 5. PAGE: DASHBOARD ---
if page == "Dashboard":
    st.title("Executive Dashboard")

    # HERO ROW
    h1, h2, h3, h4, h5 = st.columns(5)
    
    def draw_c(col, l, v, c="#FFFFFF"):
        col.markdown(f'<div class="hero-card"><div class="hero-label">{l}</div><div class="hero-val" style="color:{c}">${v:,.0f}</div></div>', unsafe_allow_html=True)

    draw_c(h1, "Net Worth", current_nw, "#D4AF37")
    draw_c(h2, "Checking", st.session_state.acct_data['Checking'])
    draw_c(h3, "Savings", st.session_state.acct_data['Savings'])
    draw_c(h4, "Retirement", st.session_state.acct_data['Retirement'])
    draw_c(h5, "Total Debt", d_total, "#FF5252")

    st.markdown("<br>", unsafe_allow_html=True)

    # ADJUSTMENT FORM
    with st.expander("🛠️ EDIT HERO BALANCES", expanded=False):
        with st.form("hero_edit_form"):
            c1, c2, c3 = st.columns(3)
            new_ch = c1.number_input("Checking", value=float(st.session_state.acct_data['Checking']))
            new_sa = c2.number_input("Savings", value=float(st.session_state.acct_data['Savings']))
            new_re = c3.number_input("Retirement", value=float(st.session_state.acct_data['Retirement']))
            
            if st.form_submit_button("PRESS TO UPDATE DASHBOARD"):
                st.session_state.acct_data = {"Checking": new_ch, "Savings": new_sa, "Retirement": new_re}
                pd.DataFrame([st.session_state.acct_data]).to_csv("aura_accounts.csv", index=False)
                st.rerun()

    st.markdown("---")
    
    # PINNED SECTION (CLEANED)
    st.markdown("### 🏛️ Wealth Progress")
    # Only showing Savings Goal now
    spent = st.session_state.exp_df[st.session_state.exp_df['Category'] == "Savings Goal"]['Amount'].sum() if not st.session_state.exp_df.empty else 0
    goal_lim = 1000
    
    st.markdown(f"""
    <div class="budget-card">
        <div class="hero-label">Savings Goal Progress</div>
        <div class="hero-val">${spent:,.0f} <span style="font-size:14px; color:#8E8E93;">/ ${goal_lim:,.0f}</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(min(float(spent/goal_lim), 1.0) if goal_lim > 0 else 0.0)

# --- 6. PAGE: DEBT PORTFOLIO ---
elif page == "Debt Portfolio":
    st.title("Debt Portfolio")
    with st.form("debt_adder", clear_on_submit=True):
        dn = st.text_input("Lender")
        db = st.number_input("Balance", min_value=0.0)
        if st.form_submit_button("Confirm Debt"):
            new_row = pd.DataFrame([[dn, db]], columns=["Name", "Balance"])
            st.session_state.debt_df = pd.concat([st.session_state.debt_df, new_row], ignore_index=True)
            st.session_state.debt_df.to_csv("aura_debt.csv", index=False)
            st.rerun()

    for i, r in st.session_state.debt_df.iterrows():
        st.markdown(f'<div class="budget-card"><b>{r["Name"]}</b>: ${r["Balance"]:,.0f}</div>', unsafe_allow_html=True)
        if st.button("Delete Entry", key=f"d_{i}"):
            st.session_state.debt_df = st.session_state.debt_df.drop(i)
            st.session_state.debt_df.to_csv("aura_debt.csv", index=False)
            st.rerun()

# --- 7. PAGE: BUDGETS ---
elif page in ["Weekly Budget", "Monthly Budget"]:
    st.title(f"{page} Management")
    with st.form("exp_adder", clear_on_submit=True):
        cat_list = ["Rent", "Groceries", "Savings Goal", "Other"]
        c_sel = st.selectbox("Category", cat_list)
        a_val = st.number_input("Amount", min_value=0.0)
        if st.form_submit_button("Log Spent"):
            new_e = pd.DataFrame([[datetime.now(), c_sel, a_val]], columns=["Date", "Category", "Amount"])
            st.session_state.exp_df = pd.concat([st.session_state.exp_df, new_e], ignore_index=True)
            st.session_state.exp_df.to_csv("aura_expenses.csv", index=False)
            st.rerun()
