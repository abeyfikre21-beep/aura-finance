import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import os

# --- 1. CORE SETTINGS & SECURITY ---
st.set_page_config(page_title="Aura Finance OS", layout="wide")
USER_PIN = "1234" 

if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔒 Aura Secure Gateway")
    pin_attempt = st.text_input("Enter PIN", type="password")
    if st.button("Unlock"):
        if pin_attempt == USER_PIN:
            st.session_state.auth = True
            st.rerun()
        else: st.error("Incorrect PIN")
    st.stop()

# --- 2. DATA VAULT ---
DB_FILE = "aura_vault.csv"
def load_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account", "Recurring"])

def save_data(df): df.to_csv(DB_FILE, index=False)

if 'df' not in st.session_state: st.session_state.df = load_data()

# --- 3. LIVE ACCOUNT ENGINE ---
# Customize your starting balances here
accounts = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
MONTHLY_BUDGET_GOAL = 3000 # Change this to your preferred monthly limit

for _, row in st.session_state.df.iterrows():
    val = row['Amount'] if row['Type'] == 'Income' else -row['Amount']
    if row['Account'] in accounts: accounts[row['Account']] += val

net_worth = sum(accounts.values())
current_month_expenses = st.session_state.df[(st.session_state.df['Type'] == 'Expense')]['Amount'].sum()

# --- 4. EXECUTIVE DASHBOARD ---
st.title("🏛️ Aura Executive Command")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Net Worth", f"${net_worth:,.2f}")
m2.metric("Checking", f"${accounts['Checking']:,.0f}")
m3.metric("Savings", f"${accounts['Savings']:,.0f}")
m4.metric("Retirement", f"${accounts['Retirement']:,.0f}")
m5.metric("Debt", f"${accounts['Debt']:,.0f}", delta_color="inverse")

# --- 5. THE BUDGET SENTINEL (NEW) ---
st.write("---")
col_goal, col_status = st.columns([2, 1])
with col_goal:
    progress = min(current_month_expenses / MONTHLY_BUDGET_GOAL, 1.0)
    bar_color = "blue" if progress < 0.7 else "orange" if progress < 0.9 else "red"
    st.write(f"**Monthly Spending Goal:** ${current_month_expenses:,.2f} / ${MONTHLY_BUDGET_GOAL:,.2f}")
    st.progress(progress)
with col_status:
    remaining = MONTHLY_BUDGET_GOAL - current_month_expenses
    if remaining > 0:
        st.success(f"✅ ${remaining:,.2f} Left to Spend")
    else:
        st.error(f"🚨 Over Budget by ${abs(remaining):,.2f}")

# --- 6. THE WORKSPACE ---
tabs = st.tabs(["📊 Analytics", "💸 Cash Flow", "🧠 AI Advisor", "🔄 Recurring", "⚙️ System"])

with tabs[0]: # ANALYTICS
    st.subheader("Expense Breakdown")
    expenses = st.session_state.df[st.session_state.df['Type'] == 'Expense']
    if not expenses.empty:
        fig = px.pie(expenses, values='Amount', names='Category', hole=0.4, template="plotly_dark", color_discrete_sequence=px.colors.sequential.Cyan_r)
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("Add expenses in 'Cash Flow' to see your budget breakdown.")

with tabs[1]: # CASH FLOW
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Log Transaction")
        t_type = st.selectbox("Type", ["Expense", "Income"])
        t_acc = st.selectbox("Account", list(accounts.keys()))
        t_cat = st.selectbox("Category", ["Rent", "Food", "Bills", "Invest", "Leisure"])
        t_amt = st.number_input("Amount", min_value=0.0)
        t_rec = st.checkbox("Recurring Bill?")
        if st.button("🚀 Commit"):
            new_row = pd.DataFrame([[datetime.now().date(), t_type, t_cat, t_amt, t_acc, t_rec]], 
                                   columns=["Date", "Type", "Category", "Amount", "Account", "Recurring"])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            save_data(st.session_state.df)
            st.toast("Transaction Saved!", icon="✅")
            st.rerun()
    with c2: st.dataframe(st.session_state.df.sort_index(ascending=False), use_container_width=True)

with tabs[2]: # AI ADVISOR
    st.subheader("🧠 Aura Insights")
    if current_month_expenses > (MONTHLY_BUDGET_GOAL * 0.8):
        st.warning("⚠️ High Burn Rate: You've used 80% of your budget. AI suggests freezing 'Leisure' spending.")
    if abs(accounts['Debt']) > 0:
        st.info(f"Strategy: Your Debt is ${abs(accounts['Debt'])}. Use 10% of next Income to clear this.")
    else:
        st.success("Wealth Mastery: No debt detected. You are in growth mode.")

with tabs[3]: # RECURRING
    st.subheader("🔄 Active Subscriptions")
    recurs = st.session_state.df[st.session_state.df['Recurring'] == True]
    if not recurs.empty: st.table(recurs[['Category', 'Amount', 'Account']])
    else: st.write("No recurring bills logged yet.")

with tabs[4]: # SETTINGS
    st.subheader("Account DNA")
    if st.button("🔓 Logout"):
        st.session_state.auth = False
        st.rerun()
    if st.button("🗑️ Wipe All Data"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.df = pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account", "Recurring"])
        st.rerun()
