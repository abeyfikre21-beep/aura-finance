import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. PREMIUM CONFIG ---
st.set_page_config(page_title="Aura Finance Pro", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 32px; color: #00f2ff; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #1c2128; border-radius: 8px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA PERSISTENCE ---
if 'transactions' not in st.session_state:
    st.session_state.transactions = pd.DataFrame(columns=["Date", "Category", "Amount", "Type"])

# Base accounts (Edit these to your real starting balances)
starting_balance = 50000 

# Calculate Real-Time Net Worth
total_spent = st.session_state.transactions[st.session_state.transactions['Type'] == 'Expense']['Amount'].sum()
total_earned = st.session_state.transactions[st.session_state.transactions['Type'] == 'Income']['Amount'].sum()
live_net_worth = starting_balance + total_earned - total_spent

# --- 3. EXECUTIVE HEADER ---
st.title("🏛️ Aura Executive Command")
st.caption(f"Real-Time Intelligence | {datetime.now().strftime('%Y-%m-%d')}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Live Net Worth", f"${live_net_worth:,.2f}")
m2.metric("Monthly Burn", f"${total_spent:,.2f}")
health_score = int(max(0, min(100, (live_net_worth / 1000)))) # Dynamic score logic
m3.metric("Health Score", f"{health_score}/100")
m4.metric("Status", "Operational" if health_score > 50 else "Watchlist")

# --- 4. THE UPGRADE TABS ---
tabs = st.tabs(["🚀 Wealth Forecast", "🧪 Scenario Lab", "💸 Transactions", "⚙️ Settings"])

with tabs[0]:
    st.subheader("Predictive Wealth Trajectory")
    months = 12
    avg_monthly_gain = 1200 # Default assumption
    dates = [datetime.now() + timedelta(days=30*i) for i in range(months)]
    forecast = [live_net_worth + (avg_monthly_gain * i) for i in range(months)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=forecast, mode='lines', name='Forecast', line=dict(color='#00f2ff', width=3)))
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.subheader("🧪 Financial Scenario Simulator")
    st.write("Adjust the sliders to see how life decisions impact your future wealth.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        one_time_cost = st.slider("One-time Purchase (e.g. Car/Gift)", 0, 50000, 0, step=500)
        monthly_cut = st.slider("Monthly Budget Cut (Savings)", 0, 2000, 0, step=50)
    
    with col_b:
        # Scenario Logic
        new_nw = live_net_worth - one_time_cost
        new_forecast = [new_nw + ((avg_monthly_gain + monthly_cut) * i) for i in range(months)]
        
        st.metric("New Projected NW (12mo)", f"${new_forecast[-1]:,.2f}", delta=f"${new_forecast[-1] - forecast[-1]:,.2f}")
        if one_time_cost > live_net_worth:
            st.error("⚠️ This purchase exceeds your current liquid assets!")

with tabs[2]:
    st.subheader("Transaction Ledger")
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.expander("➕ Log Transaction", expanded=True):
            t_date = st.date_input("Date")
            t_type = st.radio("Type", ["Expense", "Income"])
            t_amt = st.number_input("Amount", min_value=0.0)
            t_cat = st.selectbox("Category", ["Rent", "Food", "Tech", "Investing", "Misc"])
            if st.button("Commit to Ledger"):
                new_entry = pd.DataFrame([[t_date, t_cat, t_amt, t_type]], columns=["Date", "Category", "Amount", "Type"])
                st.session_state.transactions = pd.concat([st.session_state.transactions, new_entry], ignore_index=True)
                st.rerun()
    with c2:
        st.dataframe(st.session_state.transactions.sort_index(ascending=False), use_container_width=True)

with tabs[3]:
    st.subheader("Core Configuration")
    st.write("Manage your app's DNA here.")
    if st.button("🗑️ Wipe All Transactions"):
        st.session_state.transactions = pd.DataFrame(columns=["Date", "Category", "Amount", "Type"])
        st.rerun()
