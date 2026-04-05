import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & EXECUTIVE DARK THEME ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #02060E; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #D4AF37; }
    
    .hero-card {
        background: #0D1526; padding: 25px 10px; border-radius: 15px;
        border: 1px solid #1C2C4E; text-align: center; min-height: 120px;
    }
    .hero-label { font-size: 11px; color: #8E8E93; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; font-weight: 600;}
    .hero-val { font-size: 26px; font-weight: 800; color: #FFFFFF; }
    
    .budget-card {
        background: #0D1526; padding: 18px; border-radius: 12px;
        border: 1px solid #1C2C4E; margin-bottom: 10px;
    }
    .stat-label { font-size: 10px; color: #8E8E93; text-transform: uppercase; }
    .stat-val { font-size: 18px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE (Persistent Account Balances) ---
# We use a dedicated CSV to remember your account numbers even after refresh
def load_accounts():
    if os.path.exists("aura_accounts.csv"):
        return pd.read_csv("aura_accounts.csv").iloc[0].to_dict()
    return {"Checking": 8450.0, "Savings": 25000.0, "Retirement": 142000.0}

def save_accounts(data):
    pd.DataFrame([data]).to_csv("aura_accounts.csv", index=False)

if 'accounts' not in st.session_state:
    st.session_state.accounts = load_accounts()

# Load other DBs
DB_FILES = ["expenses", "budgets", "debt"]
for key in DB_FILES:
    file = f"aura_{key}.csv"
    if key not in st.session_state:
        st.session_state[key] = pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

# --- 3. NAVIGATION ---
with st.sidebar:
    st.title("🏛️ AURA")
    page = st.radio("MENU", ["Dashboard", "Monthly Budget", "Weekly Budget", "Debt"])

# --- 4. DASHBOARD RENDERER ---
def draw_hero(col, label, value, color="#FFFFFF"):
    html = f"""
    <div class="hero-card">
        <div class="hero-label">{label}</div>
        <div class="hero-val" style="color:{color}">${value:,.0f}</div>
    </div>
    """
    col.markdown(html, unsafe_allow_html=True)

if page == "Dashboard":
    st.title("Executive Dashboard")

    # Calculate Totals
    total_debt = st.session_state.debt['Balance'].sum() if not st.session_state.debt.empty else 0
    net_worth = (st.session_state.accounts['Checking'] + 
                 st.session_state.accounts['Savings'] + 
                 st.session_state.accounts['Retirement']) - total_debt

    # --- TOP HERO SECTION ---
    h1, h2, h3, h4, h5 = st.columns(5)
    draw_hero(h1, "Net Worth", net_worth, color="#D4AF37")
    draw_hero(h2, "Checking Account", st.session_state.accounts['Checking'])
    draw_hero(h3, "Savings", st.session_state.accounts['Savings'])
    draw_hero(h4, "Retirement Fund", st.session_state.accounts['Retirement'])
    draw_hero(h5, "Total Debt", total_debt, color="#FF5252")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ADJUSTMENT VAULT ---
    with st
