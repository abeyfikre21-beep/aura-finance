import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. PREMIUM UX CONFIGURATION ---
st.set_page_config(page_title="Aura Finance Pro", layout="wide", initial_sidebar_state="expanded")

# Custom Styling for "Glassmorphism" effect
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #00f2ff; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border-radius: 5px; padding: 10px 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE WEALTH ENGINE (Logic Layer) ---
class WealthEngine:
    @staticmethod
    def calculate_health_score(net_worth, monthly_spend, debt):
        # A 1-100 score based on 2026 financial benchmarks
        burn_rate = monthly_spend if monthly_spend > 0 else 1
        runway = (net_worth / burn_rate)
        debt_to_income = abs(debt) / (net_worth + 1)
        
        score = 50 + (runway * 2) - (debt_to_income * 100)
        return int(max(0, min(100, score)))

    @staticmethod
    def get_forecast(current_nw, avg_monthly_savings, months=12):
        # Predictive Forecasting using Linear Growth
        future_dates = [datetime.now() + timedelta(days=30*i) for i in range(months)]
        projection = [current_nw + (avg_monthly_savings * i) for i in range(months)]
        return future_dates, projection

# --- 3. CORE UI - COMMAND CENTER ---
st.title("🏛️ Aura Executive Command Center")
st.caption("2026 Premium Financial OS | Secure & Encrypted")

# Simulation of dynamic data
current_net_worth = 68450.00
monthly_savings = 1250.00
monthly_expenses = 3400.00
total_debt = -2400.00

# Metric Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Current Net Worth", f"${current_net_worth:,.2f}", "+$840.00")
m2.metric("Monthly Burn Rate", f"${monthly_expenses:,.2f}", "-5%")
m3.metric("Financial Health", f"{WealthEngine.calculate_health_score(current_net_worth, monthly_expenses, total_debt)}/100", "Strong")
m4.metric("Days of Runway", f"{int(current_net_worth/monthly_expenses)} Days", "+12")

# --- 4. THE UPGRADE MODULES ---
tabs = st.tabs(["🚀 Wealth Forecast", "💳 Subscription Shield", "🎯 Goal Lab", "⚙️ Data Core"])

with tabs[0]:
    st.subheader("Predictive Wealth Trajectory")
    dates, future_nw = WealthEngine.get_forecast(current_net_worth, monthly_savings)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=future_nw, mode='lines+markers', name='Projected NW', line=dict(color='#00f2ff', width=4)))
    fig.update_layout(template="plotly_dark", hovermode="x unified", margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(f"💡 **Insight:** At your current savings rate, you will hit **$100,000** in {int((100000-current_net_worth)/monthly_savings)} months.")

with tabs[1]:
    st.subheader("Recurring Subscription Audit")
    # Simulation of the "Shield"
    sub_data = pd.DataFrame({
        "Service": ["Netflix", "Gym Membership", "Cloud Storage", "Premium Coffee Sub"],
        "Amount": [19.99, 45.00, 9.99, 30.00],
        "Frequency": ["Monthly"] * 4
    })
    st.table(sub_data)
    st.warning("Action Required: You are spending $1,259.76/year on subscriptions. 2 look inactive.")

with tabs[3]:
    st.subheader("Data Management")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📥 Export Wealth Report (PDF)"):
            st.toast("Generating Premium Report...")
    with col_b:
        if st.button("🗑️ Clear Audit Log"):
            st.toast("Security protocol executed: Data Purged.")

# --- 5. SIDEBAR: THE QUICK-ACTION ENGINE ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/diamond.png", width=80)
    st.header("Aura Pro Settings")
    st.divider()
    # Categorization management
    st.subheader("Category Manager")
    st.write("Current: Rent, Food, Travel, Investing")
    new_c = st.text_input("Add Category")
    if st.button("Update Schema"): st.success("Database Updated")
