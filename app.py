import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & INTERACTIVE CSS ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #02060E; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #D4AF37; }
    
    .hero-card {
        background: linear-gradient(145deg, #0D1526, #16223D); 
        padding: 30px 15px; border-radius: 20px;
        border: 1px solid #D4AF37; text-align: center; 
        box-shadow: 0px 4px 15px rgba(212, 175, 55, 0.1);
        margin-bottom: 20px;
    }
    .detail-card {
        background: #090F1C; padding: 12px; border-radius: 10px;
        border: 1px solid #1C2C4E; text-align: left;
        margin-bottom: 10px; min-height: 85px;
    }
    .hero-label { font-size: 11px; color: #8E8E93; text-transform: uppercase; letter-spacing: 2px; font-weight: 700;}
    .hero-val { font-size: 30px; font-weight: 900; color: #FFFFFF; }
    .detail-label { font-size: 9px; color: #6C757D; text-transform: uppercase; font-weight: 600; }
    .detail-val { font-size: 17px; font-weight: 700; color: #E0E0E0; }
    .section-title { margin-top: 30px; color: #8E8E93; font-size: 10px; text-transform: uppercase; letter-spacing: 4px; text-align: center;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE (LIVE SYNC) ---
def load_data(file, defaults):
    if os.path.exists(file): return pd.read_csv(file)
    df = pd.DataFrame(defaults)
    df.to_csv(file, index=False)
    return df

# Initialize Session States
if 'acct_data' not in st.session_state:
    st.session_state.acct_data = load_data("aura_accounts.csv", [{"Checking": 0.0, "Savings": 0.0, "Retirement": 0.0}]).iloc[0].to_dict()
if 'targets' not in st.session_state:
    st.session_state.targets = load_data("aura_targets.csv", [{"WeeklyBudget": 1000.0, "MonthlyBudget": 4000.0, "NextBill": 0.0, "Emergency": 500.0}]).iloc[0].to_dict()

st.session_state.debt_df = load_data("aura_debt.csv", {"Name": [], "Balance": []})
st.session_state.exp_df = load_data("aura_expenses.csv", {"Date": [], "Category": [], "Amount": []})

# --- 3. LIVE AUTO-CALCULATIONS ---
d_total = float(st.session_state.debt_df['Balance'].sum()) if not st.session_state.debt_df.empty else 0.0
a_total = sum(st.session_state.acct_data.values())
net_worth = a_total - d_total

# Spending Logic
st.session_state.exp_df['Date'] = pd.to_datetime(st.session_state.exp_df['Date'])
now = datetime.now()
m_spent = st.session_state.exp_df[st.session_state.exp_df['Date'].dt.month == now.month]['Amount'].sum()
w_spent = st.session_state.exp_df[st.session_state.exp_df['Date'] > (now - pd.Timedelta(days=7))]['Amount'].sum()
total_spent = st.session_state.exp_df['Amount'].sum()

leftover = st.session_state.acct_data['Checking'] - total_spent
left_after_budget = st.session_state.targets['MonthlyBudget'] - m_spent

# --- 4. NAVIGATION & EDIT TOGGLE ---
with st.sidebar:
    st.title("🏛️ AURA")
    nav = st.radio("SELECT VIEW", ["📊 Dashboard", "💰 Assets", "💳 Debt Portfolio", "🗓️ Weekly Budget", "📅 Monthly Budget", "👤 Profile"])
    st.markdown("---")
    edit_mode = st.toggle("🛠️ Edit Dashboard Mode", help="Turn this on to click and change card values.")

# --- 5. PAGE: DASHBOARD ---
if nav == "📊 Dashboard":
    if edit_mode:
        st.warning("EDIT MODE ACTIVE: Change values below and click 'Save Changes' at the bottom.")
        with st.form("global_edit"):
            st.markdown("### Edit Principal Balances")
            c1, c2, c3 = st.columns(3)
            new_ch = c1.number_input("Checking", value=float(st.session_state.acct_data['Checking']))
            new_sa = c2.number_input("Savings", value=float(st.session_state.acct_data['Savings']))
            new_re = c3.number_input("Retirement", value=float(st.session_state.acct_data['Retirement']))
            
            st.markdown("### Edit Budget Targets & Bills")
            t1, t2, t3, t4 = st.columns(4)
            new_wb = t1.number_input("Weekly Budget", value=float(st.session_state.targets['WeeklyBudget']))
            new_mb = t2.number_input("Monthly Budget", value=float(st.session_state.targets['MonthlyBudget']))
            new_nb = t3.number_input("Next Bill Amt", value=float(st.session_state.targets['NextBill']))
            new_em = t4.number_input("Emergency Reserve", value=float(st.session_state.targets['Emergency']))
            
            if st.form_submit_button("💾 SAVE ALL CHANGES"):
                st.session_state.acct_data = {"Checking": new_ch, "Savings": new_sa, "Retirement": new_re}
                st.session_state.targets = {"WeeklyBudget": new_wb, "MonthlyBudget": new_mb, "NextBill": new_nb, "Emergency": new_em}
                pd.DataFrame([st.session_state.acct_data]).to_csv("aura_accounts.csv", index=False)
                pd.DataFrame([st.session_state.targets]).to_csv("aura_targets.csv", index=False)
                st.rerun()
    else:
        # --- DISPLAY MODE (Live Updated) ---
        st.markdown('<div class="section-title">Principal Wealth</div>', unsafe_allow_html=True)
        h_cols = st.columns(5)
        def draw_h(col, l, v, c="#FFFFFF"):
            col.markdown(f'<div class="hero-card"><div class="hero-label">{l}</div><div class="hero-val" style="color:{c}">${v:,.0f}</div></div>', unsafe_allow_html=True)
        
        draw_h(h_cols[0], "Net Worth", net_worth, "#D4AF37")
        draw_h(h_cols[1], "Checking", st.session_state.acct_data['Checking'])
        draw_h(h_cols[2], "Savings", st.session_state.acct_data['Savings'])
        draw_h(h_cols[3], "Retirement", st.session_state.acct_data['Retirement'])
        draw_h(h_cols[4], "Total Debt", d_total, "#FF5252")

        st.markdown('<div class="section-title">Live Flow & Targets</div>', unsafe_allow_html=True)
        def draw_d(col, l, v):
            col.markdown(f'<div class="detail-card"><div class="detail-label">{l}</div><div class="detail-val">${v:,.0f}</div></div>', unsafe_allow_html=True)

        d_r1 = st.columns(4)
        draw_d(d_r1[0], "Left After Budget", left_after_budget)
        draw_d(d_r1[1], "Total Spent", total_spent)
        draw_d(d_r1[2], "Weekly Budget", st.session_state.targets['WeeklyBudget'])
        draw_d(d_r1[3], "Weekly Spent (Live)", w_spent)

        d_r2 = st.columns(4)
        draw_d(d_r2[0], "Monthly Budget", st.session_state.targets['MonthlyBudget'])
        draw_d(d_r2[1], "Monthly Spent (Live)", m_spent)
        draw_d(d_r2[2], "Next Bill", st.session_state.targets['NextBill'])
        draw_d(d_r2[3], "Emergency Expense", st.session_state.targets['Emergency'])

        d_r3 = st.columns(2)
        draw_d(d_r3[0], "Leftover Money", leftover)
        draw_d(d_r3[1], "AI Recommendations", 0)

# --- CATEGORIES REMAIN UNTOUCHED & PERSISTENT ---
elif nav == "💳 Debt Portfolio":
    st.title("Debt Portfolio")
    # [Existing Debt Logic...]
