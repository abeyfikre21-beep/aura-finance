import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import os

# --- 1. MOBILE-FIRST SETTINGS ---
st.set_page_config(
    page_title="Aura Finance",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed" # Better for small screens
)

# Custom CSS to hide Streamlit headers and make it look like a native app
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    [data-testid="stMetricValue"] { font-size: 28px !important; }
    </style>
    """, unsafe_allow_html=True)

USER_PIN = "1234" 

if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔒 Aura Mobile")
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

filtered_df = st.session_state.df[st.session_state.df['Date'] >= start_date]
period_expenses = filtered_df[filtered_df['Type'] == 'Expense']['Amount'].sum()

# --- 4. LIVE ACCOUNT ENGINE ---
accounts = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
for _, row in st.session_state.df.iterrows():
    val = row['Amount'] if row['Type'] == 'Income' else -row['Amount']
    if row['Account'] in accounts: accounts[row['Account']] += val

# --- 5. MOBILE DASHBOARD ---
st.title("🏛️ Aura Executive")
# Metrics stacked for mobile readability
m1, m2 = st.columns(2)
m1.metric("Net Worth", f"${sum(accounts.values()):,.0f}")
m2.metric("Checking", f"${accounts['Checking']:,.0f}")

m3, m4 = st.columns(2)
m3.metric("Savings", f"${accounts['Savings']:,.0f}")
m4.metric("Debt", f"${accounts['Debt']:,.0f}", delta_color="inverse")

st.write("---")
progress = min(period_expenses / budget_goal, 1.0) if budget_goal > 0 else 0
st.write(f"**Budget:** ${period_expenses:,.0f} / ${budget_goal:,.0f}")
st.progress(progress)

# --- 6. NAVIGATION TABS ---
tabs = st.tabs(["💸 Log", "📊 Stats", "🧠 AI", "⚙️"])

with tabs[0]: # Optimized Log for Mobile
    st.subheader("New Entry")
    t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    t_amt = st.number_input("Amount", min_value=0.0, step=1.0)
    t_cat = st.selectbox("Category", ["Food", "Transport", "Housing", "Bills", "Invest", "Leisure"])
    t_acc = st.selectbox("Account", list(accounts.keys()))
    if st.button("🚀 Save Transaction", use_container_width=True):
        new_row = pd.DataFrame([[today, t_type, t_cat, t_amt, t_acc]], 
                               columns=["Date", "Type", "Category", "Amount", "Account"])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.session_state.df.to_csv(DB_FILE, index=False)
        st.toast("Saved!")
        st.rerun()

with tabs[1]:
    st.subheader("Spending Analysis")
    exp_df = filtered_df[filtered_df['Type']=='Expense']
    if not exp_df.empty:
        fig = px.pie(exp_df, values='Amount', names='Category', hole=0.5, template="plotly_dark")
        fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(filtered_df.sort_values("Date", ascending=False), use_container_width=True)

with tabs[2]:
    st.subheader("AI Advisor")
    total_liquid = accounts['Checking'] + accounts['Savings']
    daily_burn = period_expenses / ((today - start_date).days + 1)
    if daily_burn > 0:
        runway = total_liquid / daily_burn
        st.info(f"🛡️ **Runway:** {int(runway)} Days Remaining")
    st.success("Strategy: Buy the dip in Retirement fund.")

with tabs[3]:
    if st.button("Logout", use_container_width=True):
        st.session_state.auth = False
        st.rerun()
