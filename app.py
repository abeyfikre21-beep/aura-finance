import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# --- 1. CONFIG & REFINED DARK THEME ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #02060E; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #D4AF37; }
    
    @media (min-width: 1024px) { .main-container { max-width: 600px; margin: 0 auto; } }

    .metric-card {
        background: #0D1526; padding: 20px; border-radius: 15px;
        border: 1px solid #1C2C4E; text-align: center; margin-bottom: 15px;
    }
    .hero-label { font-size: 10px; color: #8E8E93; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px;}
    .hero-val { font-size: 24px; font-weight: 800; color: #FFFFFF; }
    .budget-card {
        background: #0D1526; padding: 15px; border-radius: 12px;
        border: 1px solid #1C2C4E; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
DB_FILES = ["expenses", "budgets", "leftover", "debt"]

def load_vault(key):
    file = f"aura_{key}.csv"
    if os.path.exists(file):
        df = pd.read_csv(file)
        if 'Date' in df.columns: df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame()

for key in DB_FILES:
    if key not in st.session_state:
        st.session_state[key] = load_vault(key)

# --- 3. NAVIGATION & SHARED DATA ---
with st.sidebar:
    st.title("🏛️ AURA")
    page = st.radio("MENU", ["Dashboard", "Monthly Budget", "Weekly Budget", "Debt", "Assistant"])
    st.markdown("---")
    
    # Static Account Input (Adjust these values as they change)
    st.subheader("🏦 Account Balances")
    val_checking = st.number_input("Checking Balance", value=8450, step=100)
    val_savings = st.number_input("Savings Balance", value=25000, step=500)
    val_retire = st.number_input("Retirement Fund", value=142000, step=1000)
    
    total_debt = st.session_state.debt['Balance'].sum() if not st.session_state.debt.empty else 0
    net_worth = (val_checking + val_savings + val_retire) - total_debt

# --- 4. DASHBOARD: TOP HERO SECTION ---
if page == "Dashboard":
    st.title("Financial Command Center")
    
    # TOP HERO ROW
    h1, h2, h3, h4, h5 = st.columns(5)
    
    with h1: st.markdown(f'<div class="metric-card"><div class="hero-label">Net Worth</div><div class="hero-val">${net_worth:,.0f}</div></div>', unsafe_allow_html=True)
    with h2: st.markdown(f'<div class="metric-card"><div class="hero-label">Checking</div><div class="hero-val">${val_checking:,.0f}</div></div>', unsafe_allow_html=True)
    with h3: st.markdown(f'<div class="metric-card"><div class="hero-label">Savings</div><div class="hero-val">${val_savings:,.0f}</div></div>', unsafe_allow_html=True)
    with h4: st.markdown(f'<div class="metric-card"><div class="hero-label">Retirement</div><div class="hero-val">${val_retire:,.0f}</div></div>', unsafe_allow_html=True)
    with h5: st.markdown(f'<div class="metric-card"><div class="hero-label">Total Debt</div><div class="hero-val" style="color:#FF5252;">${total_debt:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # CHART SECTION
    if not st.session_state.budgets.empty:
        disp_data = []
        for _, b_row in st.session_state.budgets.iterrows():
            spent = st.session_state.expenses[st
