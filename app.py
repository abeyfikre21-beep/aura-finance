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
    section[data-testid="stSidebar"] { background-color: #121212 !important; border-right: 1px solid #D4AF37; }
    div[data-testid="stMetric"] {
        background: rgba(28, 28, 30, 0.9);
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 15px;
        padding: 15px;
    }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; font-weight: 800 !important; }
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
        try:
            df = pd.read_csv(DB_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except:
            return pd.DataFrame(columns=["Date", "Category", "Amount", "Period", "Account"])
    return pd.DataFrame(columns=["Date", "Category", "Amount", "Period", "Account"])

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🏛️ Aura Menu")
    st.markdown("---")
    st.markdown("👤 **Profile**")
    view_mode = st.radio("View Cycle", ["Weekly", "Monthly"])
    target = st.number_input(f"Target {view_mode} Budget", value=1200 if view_mode == "Weekly" else 4500)
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

# Filter current data
current_data = df[df['Date'] >= pd.to_datetime(start_date)]
total_spent = current_data['Amount'].sum() if not current_data.empty else 0.0
remaining = target - total_spent

# --- 5. INTERFACE ---
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

with tabs[0]: 
    st.subheader("New Entry")
    cat = st.selectbox("Category", ["Housing", "Insurance", "Car", "Groceries", "Gas", "Phone", "Gym", "Subscription", "Other"])
    amt = st.number_input("Amount Paid ($)", min_value=0.0, step=0.01)
    date_entry = st.date_input("Transaction Date", datetime.now())
    
    if
