import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & HIERARCHICAL CSS ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #02060E; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #D4AF37; }
    
    /* --- MAIN HERO CARDS (BIG & BOLD) --- */
    .hero-card {
        background: linear-gradient(145deg, #0D1526, #16223D); 
        padding: 30px 15px; border-radius: 20px;
        border: 1px solid #D4AF37; text-align: center; 
        box-shadow: 0px 4px 15px rgba(212, 175, 55, 0.1);
        margin-bottom: 20px;
    }
    .hero-label { font-size: 12px; color: #8E8E93; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 12px; font-weight: 700;}
    .hero-val { font-size: 32px; font-weight: 900; color: #FFFFFF; }
    
    /* --- DETAIL CARDS (SMALLER & SUBTLE) --- */
    .detail-card {
        background: #090F1C; padding: 12px; border-radius: 10px;
        border: 1px solid #1C2C4E; text-align: left;
        margin-bottom: 10px; min-height: 80px;
    }
    .detail-label { font-size: 9px; color: #6C757D; text-transform: uppercase; font-weight: 600; letter-spacing: 1px; }
    .detail-val { font-size: 16px; font-weight: 700; color: #E0E0E0; margin-top: 4px; }
    
    .section-title { 
        margin-top: 40px; margin-bottom: 15px; color: #8E8E93; 
        font-size: 11px; text-transform: uppercase; letter-spacing: 4px; font-weight: 800;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PERSISTENCE ENGINE ---
def load_csv(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    df = pd.DataFrame(columns=columns)
    df.to_csv(file, index=False)
    return df

if 'acct_data' not in st.session_state:
    if os.path.exists("aura_accounts.csv"): 
        st.session_state.acct_data = pd.read_csv("aura_accounts.csv").iloc[0].to_dict()
    else: 
        st.session_state.acct_data = {"Checking": 0.0, "Savings": 0.0, "Retirement": 0.0}

st.session_state.debt_df = load_csv("aura_debt.csv", ["Name", "Balance"])
st.session_state.exp_df = load_csv("aura_expenses.csv", ["Date", "Category", "Amount"])

# --- 3. MATH ---
d_total = float(st.session_state.debt_df['Balance'].sum()) if not st.session_state.debt_df.empty else 0.0
a_total = sum(st.session_state.acct_data.values())
current_nw = a_total - d_total
total_spent = st.session_state.exp_df['Amount'].sum() if not st.session_state.exp_df.empty else 0.0

# --- 4. NAVIGATION ---
with st.sidebar:
    st.title("🏛️ AURA")
    nav = st.radio("SELECT VIEW", [
        "📊 Dashboard", "💰 Assets (Wealth)", "💳 Debt Portfolio", 
        "🗓️ Weekly Budget", "📅 Monthly Budget", "📈 Insights & History", 
        "🤖 Assistant", "👤 Profile", "🎨 Appearance"
    ])

# --- 5. PAGE: DASHBOARD ---
if nav == "📊 Dashboard":
    st.markdown('<div class="section-title">Principal Financial Status</div>', unsafe_allow_html=True)
    h1, h2, h3, h4, h5 = st.columns(5)
    
    def draw_hero(col, l, v, c="#FFFFFF"):
        col.markdown(f'<div class="hero-card"><div class="hero-label">{l}</div><div class="hero-val" style="color:{c}">${v:,.0f}</div></div>', unsafe_allow_html=True)

    draw_hero(h1, "Net Worth", current_nw, "#D4AF37")
    draw_hero(h2, "Checking", st.session_state.acct_data['Checking'])
    draw_hero(h3, "Savings", st.session_state.acct_data['Savings'])
    draw_hero(h4, "Retirement Fund", st.session_state.acct_data['Retirement'])
    draw_hero(h5, "Total Debt", d_total, "#FF5252")

    st.markdown('<div class="section-title">Budgetary Metrics & Flow</div>', unsafe_allow_html=True)
    
    def draw_detail(col, l, v):
        col.markdown(f'<div class="detail
