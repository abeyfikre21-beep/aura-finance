import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf
from datetime import datetime
import os

# --- 1. DARK MODE & SIDEBAR DRAWER STYLING ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #050505; color: #FFFFFF; }
    
    /* Sidebar (The Drawer) Styling */
    section[data-testid="stSidebar"] {
        background-color: #121212 !important;
        border-right: 1px solid rgba(212, 175, 55, 0.2);
        width: 300px !important;
    }
    
    /* Metrics Styling */
    div[data-testid="stMetric"] {
        background: rgba(28, 28, 30, 0.8);
        border: 1px solid rgba(212, 175, 55, 0.2);
        padding: 20px;
        border-radius: 20px;
    }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; font-size: 32px !important; font-weight: 800 !important; }
    
    /* Hero Section */
    .hero-container {
        background: linear-gradient(180deg, #1c1c1e 0%, #050505 100%);
        border: 1px solid rgba(212, 175, 55, 0.1);
        padding: 40px 20px;
        border-radius: 25px;
        text-align: center;
        margin-bottom: 20px;
    }
    .hero-amount { color: #D4AF37; font-size: 52px; font-weight: 900; }
    
    /* Buttons & Inputs */
    .stButton>button {
        background-color: #D4AF37 !important;
        color: black !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
DB_FILE = "aura_vault.csv"
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df.dropna(subset=['Date'])
    return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account"])

if 'df' not in st.session_state: st.session_state.df = load_data()

# --- 3. THE "ROCKET MONEY" DRAWER (SIDEBAR) ---
with st.sidebar:
    st.markdown("### 🏛️ Aura Executive")
    st.markdown("---")
    
    # Profile Section
    st.markdown("👤 **Profile**")
    st.caption("Aura Member since 2024")
    if st.button("Edit Profile", use_container_width=True):
        st.toast("Profile settings coming soon")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # App Settings
    st.markdown("⚙️ **App Settings**")
    appearance = st.selectbox("Appearance", ["Executive Dark", "Stone Light", "Midnight Blue"])
    currency = st.selectbox("Currency", ["USD ($)", "EUR (€)", "GBP (£)"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Financial Goals
    st.markdown("🎯 **Wealth Strategy**")
    NW_GOAL = st.number_input("Net Worth Target", value=100000)
    
    st.markdown("---")
    if st.button("🔒 Logout", use_container_width=True):
        st.stop()

# --- 4. CALCULATIONS ---
acc_vals = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
for _, r in st.session_state.df.iterrows():
    val = r['Amount'] if r['Type'] == 'Income' else -r['Amount']
    if r['Account'] in acc_vals: acc_vals[r['Account']] += val
total_nw = sum(acc_vals.values())

# --- 5. MAIN DASHBOARD ---
st.markdown(f"""
    <div class="hero-container">
        <div style="color: #8E8E93; font-size: 12px; letter-spacing: 2px;">TOTAL NET WORTH</div>
        <div class="hero-amount">${total_nw:,.0f}</div>
        <div style="color: #D4AF37; font-size: 14px;">MILESTONE: {min(total_nw/NW_GOAL*100, 100.0):.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("Cash", f"${acc_vals['Checking'] + acc_vals['Savings']:,.0f}")
c2.metric("Invested", f"${acc_vals['Retirement']:,.0f}")
c3.metric("Debt", f"${abs(acc_vals['Debt']):,.0f}")

tabs = st.tabs(["🏛️ Terminal", "💸 Transactions", "📊 Analysis"])

with tabs[0]: # TERMINAL
    chart_data = pd.DataFrame(np.random.randn(20, 1).cumsum() + 100, columns=['Value'])
    fig = px.line(chart_data, template="plotly_dark", color_discrete_sequence=['#D4AF37'])
    fig.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]: # TRANSACTIONS
    t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    t_amt = st.number_input("Amount", min_value=0.0)
    t_cat = st.selectbox("Category", ["Food", "Invest", "Bills", "Housing"])
    t_acc = st.selectbox("Account", list(acc_vals.keys()))
    if st.button("🚀 Commit to Vault", use_container_width=True):
        new_row = pd.DataFrame([[pd.to_datetime(datetime.now().date()), t_type, t_cat, t_amt, t_acc]], columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.session_state.df.to_csv(DB_FILE, index=False)
        st.rerun()

with tabs[2]: # ANALYSIS
    if not st.session_state.df.empty:
        fig = px.pie(st.session_state.df, values='Amount', names='Category', hole=0.5, template="plotly_dark", color_discrete_sequence=['#D4AF37', '#1c1c1e', '#8E8E93'])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Log a transaction to see your wealth distribution.")
