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
        else: st.error("Incorrect PIN")
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
            return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account"])
    return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account"])

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
# Base Balances
accounts = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
for _, row in st.session_state.df.iterrows():
    val = row['Amount'] if row['Type'] == 'Income' else -row['Amount']
    if row['Account'] in accounts: accounts[row['Account']] += val

# --- 5. EXECUTIVE DASHBOARD ---
st.title(f"🏛️ Aura Executive Command")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Net Worth", f"${sum(accounts.values()):,.2f}")
m2.metric("Checking", f"${accounts['Checking']:,.0f}")
m3.metric("Savings", f"${accounts['Savings']:,.0f}")
m4.metric("Retirement", f"${accounts['Retirement']:,.0f}")
m5.metric("Debt", f"${accounts['Debt']:,.0f}", delta_color="inverse")

st.write("---")
progress = min(period_expenses / budget_goal, 1.0) if budget_goal > 0 else 0
st.write(f"**{view_mode} Spending Progress**")
st.progress(progress)

# --- 6. WORKSPACE ---
tabs = st.tabs(["📊 Analytics", "💸 Cash Flow", "🧠 AI Advisor", "⚙️ System"])

with tabs[0]: 
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Spending by Category")
        exp_df = filtered_df[filtered_df['Type']=='Expense']
        if not exp_df.empty:
            fig = px.pie(exp_df, values='Amount', names='Category', hole=0.5, 
                         color_discrete_sequence=px.colors.sequential.Tealgrn)
            fig.update_layout(showlegend=False, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No data for this period.")
    with col_b:
        st.subheader("Daily Momentum")
        if not filtered_df.empty:
            trend = filtered_df.groupby('Date')['Amount'].sum().reset_index()
            fig2 = px.area(trend, x='Date', y='Amount', template="plotly_dark", color_discrete_sequence=['#00f2ff'])
            st.plotly_chart(fig2, use_container_width=True)

with tabs[1]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Log Entry")
        t_date = st.date_input("Date", value=datetime.now().date())
        t_type = st.selectbox("Type", ["Expense", "Income"])
        t_acc = st.selectbox("Account", list(accounts.keys()))
        t_cat = st.selectbox("Category", ["Housing", "Food & Drink", "Transport", "Utilities", "Shopping", "Entertainment", "Investments", "Medical", "Misc"])
        t_amt = st.number_input("Amount", min_value=0.0)
        if st.button("🚀 Commit to Vault"):
            new_row = pd.DataFrame([[pd.to_datetime(t_date), t_type, t_cat, t_amt, t_acc]], 
                                   columns=["Date", "Type", "Category", "Amount", "Account"])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            st.session_state.df.to_csv(DB_FILE, index=False)
            st.toast("Transaction Encrypted")
            st.rerun()
    with c2: st.dataframe(filtered_df.sort_values("Date", ascending=False), use_container_width=True)

with tabs[2]:
    st.subheader("🧠 Aura AI Advisor")
    total_liquid = accounts['Checking'] + accounts['Savings']
    daily_burn = period_expenses / ((today - start_date).days + 1)
    
    st.markdown(f"### **Financial Vitals**")
    st.write(f"Your 'Burn Rate' is **${daily_burn:,.2f} / day**.")
    
    if daily_burn > 0:
        runway = total_liquid / daily_burn
        st.info(f"🛡️ **Cash Runway:** At this rate, your liquid cash will last **{int(runway)} days**.")
    
    if accounts['Debt'] < 0:
        st.warning(f"⚠️ **Debt Alert:** Your debt is at ${abs(accounts['Debt'])}. AI suggests allocating 15% of your next 'Income' entry to this.")
    else:
        st.success("💎 **Growth Mode:** You are debt-free. All new income is pure wealth generation.")

with tabs[3]:
    if st.button("🗑️ Factory Reset Data"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.df = pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account"])
        st.rerun()
