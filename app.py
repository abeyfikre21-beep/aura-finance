import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import os

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #FFFFFF; }
    header { visibility: hidden; }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] { background-color: #121212 !important; border-right: 1px solid #D4AF37; }
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(28, 28, 30, 0.9);
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 15px;
        padding: 15px;
    }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; font-weight: 800 !important; }
    
    /* Hero Section */
    .hero {
        background: linear-gradient(180deg, #1c1c1e, #050505);
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        border: 1px solid rgba(212, 175, 55, 0.1);
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
DB_FILE = "aura_vault.csv"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame(columns=["Date", "Category", "Amount", "Period", "Account"])

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- 3. SIDEBAR (ROCKET MONEY STYLE) ---
with st.sidebar:
    st.title("🏛️ Aura Menu")
    st.markdown("---")
    
    st.markdown("👤 **Profile**")
    st.caption("Executive Account")
    
    st.markdown("<br>⚙️ **Budget Preferences**", unsafe_allow_html=True)
    view_mode = st.radio("View Cycle", ["Weekly", "Monthly"])
    
    # Financial Targets
    target = st.number_input(f"Target {view_mode} Spending", value=1200 if view_mode == "Weekly" else 4500)
    
    st.markdown("---")
    if st.button("🗑️ Reset All Data"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.df = pd.DataFrame(columns=["Date", "Category", "Amount", "Period", "Account"])
        st.rerun()

# --- 4. CALCULATIONS ---
df = st.session_state.df
today = datetime.now()

if view_mode == "Weekly":
    start_date = today - timedelta(days=today.weekday())
    label = "This Week"
else:
    start_date = today.replace(day=1)
    label = "This Month"

# Filter data for the current period
current_data = df[df['Date'] >= pd.to_datetime(start_date)]
total_spent = current_data['Amount'].sum()
remaining = target - total_spent

# --- 5. MAIN INTERFACE ---
st.markdown(f"""
    <div class="hero">
        <div style="color: #8E8E93; font-size: 12px; letter-spacing: 2px;">{label.upper()} SPENDING</div>
        <div style="color: #D4AF37; font-size: 48px; font-weight: 900;">${total_spent:,.2f}</div>
        <div style="color: {'#4CAF50' if remaining > 0 else '#FF5252'};">
            {'Remaining' if remaining > 0 else 'Over Budget'}: ${abs(remaining):,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

tabs = st.tabs(["💸 Log Expense", "📂 Expense Vault", "📊 Insights"])

with tabs[0]: # LOGGING PAGE
    st.subheader("New Entry")
    
    # Specific Life Categories
    cat = st.selectbox("Category", [
        "Housing", "Insurance", "Car", "Groceries", 
        "Gas", "Phone", "Gym", "Subscription", "Other"
    ])
    
    # Manual Amount Input
    amt = st.number_input("Amount Paid ($)", min_value=0.0, step=0.01, format="%.2f")
    
    date_entry = st.date_input("Transaction Date", datetime.now())
    
    if st.button("🚀 Secure Entry", use_container_width=True):
        new_entry = pd.DataFrame([[pd.to_datetime(date_entry), cat, amt, view_mode, "Primary"]], 
                                 columns=["Date", "Category", "Amount", "Period", "Account"])
        st.session_state.df = pd.concat([st.session_state.df, new_entry], ignore_index=True)
        st.session_state.df.to_csv(DB_FILE, index=False)
        st.success(f"Added ${amt} to {cat}")
        st.rerun()

with tabs[1]: # VAULT (DELETE/EDIT)
    st.subheader("Expense Management")
    if df.empty:
        st.info("No expenses logged yet.")
    else:
        # Display the table with a delete option
        for i, row in df.sort_values(by="Date", ascending=False).iterrows():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.write(f"**{row['Date'].strftime('%Y-%m-%d')}**")
            c2.write(f"{row['Category']}")
            c3.write(f"${row['Amount']:,.2f}")
            if c4.button("🗑️", key=f"del_{i}"):
                st.session_state.df = st.session_state.df.drop(i)
                st.session_state.df.to_csv(DB_FILE, index=False)
                st.rerun()
            st.markdown("---")

with tabs[2]: # INSIGHTS
    st.subheader("Spending Breakdown")
    if not current_data.empty:
        fig = px.pie(current_data, values='Amount', names='Category', hole=0.6,
                     template="plotly_dark", color_discrete_sequence=px.colors.sequential.Gold_r)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Awaiting data for analysis.")
