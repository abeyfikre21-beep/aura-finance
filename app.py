import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import os

# --- 1. CORE SETTINGS ---
st.set_page_config(page_title="Aura Finance OS", layout="wide")
USER_PIN = "1234" 

if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔒 Aura Secure Gateway")
    pin_input = st.text_input("Enter PIN", type="password")
    if st.button("Unlock"): 
        if pin_input == USER_PIN:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Incorrect PIN")
    st.stop()

# --- 2. DATA VAULT ---
DB_FILE = "aura_vault.csv"
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except:
            return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account", "Recurring"])
    return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account", "Recurring"])

if 'df' not in st.session_state: st.session_state.df = load_data()

# --- 3. TEMPORAL LOGIC ---
st.sidebar.title("🕒 Time Horizon")
view_mode = st.sidebar.selectbox("View Range", ["This Week", "This Month", "This Year"])

today = pd.to_datetime(datetime.now().date())
if view_mode == "This Week":
    start_date = today - timedelta(days=today.weekday())
    budget_goal = 750 
elif view_mode == "This Month":
    start_date = today.replace(day=1)
    budget_goal = 3000
else:
    start_date = today.replace(month=1, day=1)
    budget_goal = 36000

# Filter data
filtered_df = st.session_state.df[st.session_state.df['Date'] >= start_date]
period_expenses = filtered_df[filtered_df['Type'] == 'Expense']['Amount'].sum()

# --- 4. LIVE ACCOUNT ENGINE ---
accounts = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
for _, row in st.session_state.df.iterrows():
    val = row['Amount'] if row['Type'] == 'Income' else -row['Amount']
    if row['Account'] in accounts: accounts[row['Account']] += val

# --- 5. EXECUTIVE DASHBOARD ---
st.title(f"🏛️ Aura Executive Command")
st.caption(f"Viewing Perspective: {view_mode}")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Net Worth", f"${sum(accounts.values()):,.2f}")
m2.metric("Checking", f"${accounts['Checking']:,.0f}")
m3.metric("Savings", f"${accounts['Savings']:,.0f}")
m4.metric("Retirement", f"${accounts['Retirement']:,.0f}")
m5.metric("Debt", f"${accounts['Debt']:,.0f}", delta_color="inverse")

# --- 6. BUDGET SENTINEL ---
st.write("---")
progress = min(period_expenses / budget_goal, 1.0) if budget_goal > 0 else 0
st.write(f"**{view_mode} Spending:** ${period_expenses:,.2f} / ${budget_goal:,.2f}")
st.progress(progress)

# --- 7. WORKSPACE ---
tabs = st.tabs(["📊 Analytics", "💸 Cash Flow", "🧠 AI Advisor", "⚙️ System"])

with tabs[0]: 
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Category Breakdown")
        expenses_only = filtered_df[filtered_df['Type']=='Expense']
        if not expenses_only.empty:
            fig = px.pie(expenses_only, values='Amount', names='Category', hole=0.4, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses found for this period.")
    with col_b:
        st.subheader("Spending Trend")
        if not filtered_df.empty:
            trend = filtered_df.groupby('Date')['Amount'].sum().reset_index()
            fig2 = px.line(trend, x='Date', y='Amount', template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)

with tabs[1]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Log Transaction")
        t_date = st.date_input("Date", value=datetime.now().date())
        t_type = st.selectbox("Type", ["Expense", "Income"])
        t_
