import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #02060E; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #D4AF37; }
    .hero-card {
        background: #0D1526; padding: 20px 10px; border-radius: 15px;
        border: 1px solid #1C2C4E; text-align: center; min-height: 110px;
    }
    .hero-label { font-size: 11px; color: #8E8E93; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; font-weight: 600;}
    .hero-val { font-size: 24px; font-weight: 800; color: #FFFFFF; }
    .budget-card {
        background: #0D1526; padding: 18px; border-radius: 12px;
        border: 1px solid #1C2C4E; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE: STATE INITIALIZATION ---
if 'acct_data' not in st.session_state:
    if os.path.exists("aura_accounts.csv"):
        st.session_state.acct_data = pd.read_csv("aura_accounts.csv").iloc[0].to_dict()
    else:
        st.session_state.acct_data = {"Checking": 8450.0, "Savings": 25000.0, "Retirement": 142000.0}

if 'debt_df' not in st.session_state:
    if os.path.exists("aura_debt.csv"): st.session_state.debt_df = pd.read_csv("aura_debt.csv")
    else: st.session_state.debt_df = pd.DataFrame(columns=["Name", "Balance"])

if 'exp_df' not in st.session_state:
    if os.path.exists("aura_expenses.csv"): st.session_state.exp_df = pd.read_csv("aura_expenses.csv")
    else: st.session_state.exp_df = pd.DataFrame(columns=["Date", "Category", "Amount"])

# --- 3. MATH CALCULATIONS ---
d_total = float(st.session_state.debt_df['Balance'].sum()) if not st.session_state.debt_df.empty else 0.0
a_total = sum(st.session_state.acct_data.values())
current_nw = a_total - d_total

# --- 4. NAVIGATION ---
with st.sidebar:
    st.title("🏛️ AURA")
    page = st.radio("MENU", ["Dashboard", "Debt Portfolio", "Weekly Budget", "Monthly Budget"])

# --- 5. PAGE: DASHBOARD ---
if page == "Dashboard":
    st.title("Executive Dashboard")

    # HERO ROW
    h1, h2, h3, h4, h5 = st.columns(5)
    
    def draw_c(col, l, v, c="#FFFFFF"):
        col.markdown(f'<div class="hero-card"><div class="hero-label">{l}</div><div class="hero-val" style="color:{c}">${v:,.0f}</div></div>', unsafe_allow_html=True)

    draw_c(h1, "Net Worth", current_nw, "#D4AF37")
    draw_c(h2, "Checking", st.session_state.acct_data['Checking'])
    draw_c(h3, "Savings", st.session_state.acct_data['Savings'])
    draw_c(h4, "Retirement", st.session_state.acct_data['Retirement'])
    draw_c(h5, "Total Debt", d_total, "#FF
