import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf
from datetime import datetime
import os
from PIL import Image

# --- 1. QUIET LUXURY THEME (Stone & Navy) ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');

    /* Background & Main Text */
    .stApp { background-color: #F9F7F5; color: #1A1A1A; }
    
    /* Typography */
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #0A192F !important; font-weight: 700 !important; }
    p, span, label, div { font-family: 'Inter', sans-serif !important; }

    /* The "Hero Card" */
    .hero-card {
        background: #0A192F;
        color: white;
        padding: 40px;
        border-radius: 24px;
        box-shadow: 0 20px 40px rgba(10, 25, 47, 0.1);
        margin-bottom: 30px;
        text-align: center;
    }
    .hero-label { font-size: 14px; opacity: 0.7; text-transform: uppercase; letter-spacing: 2px; }
    .hero-number { font-size: 64px; font-family: 'Playfair Display', serif; margin: 10px 0; }

    /* Content Cards */
    div[data-testid="stMetric"] {
        background: white !important;
        border: 1px solid #E5E1DA !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03) !important;
        border-radius: 16px !important;
        padding: 20px !important;
    }
    
    /* Custom Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent !important;
        border: none !important;
        color: #666 !important;
        font-weight: 600 !important;
    }
    .stTabs [aria-selected="true"] { color: #0A192F !important; border-bottom: 2px solid #0A192F !important; }

    /* Progress Bar */
    .stProgress > div > div > div > div { background-color: #2D5A27; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTH & DATA ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<div style='text-align:center; padding-top:100px;'><h1>🏛️ Aura</h1><p>Private Wealth Access</p></div>", unsafe_allow_html=True)
    if st.text_input("Vault PIN", type="password", label_visibility="collapsed") == "1234":
        st.session_state.auth = True
        st.rerun()
    st.stop()

DB_FILE, IMG_DIR = "aura_vault.csv", "receipts"
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account", "Receipt"])

st.session_state.df = load_data()

# --- 3. LOGIC ---
acc_vals = {"Checking": 5200, "Savings": 18400, "Retirement": 52000, "Debt": -1200}
for _, r in st.session_state.df.iterrows():
    if pd.notnull(r['Amount']):
        v = r['Amount'] if r['Type'] == 'Income' else -r['Amount']
        if r['Account'] in acc_vals: acc_vals[r['Account']] += v

total_nw = sum(acc_vals.values())
NW_GOAL = st.sidebar.number_input("Wealth Goal", value=100000)

# --- 4. TOP AREA: THE HERO ---
st.markdown(f"""
    <div class="hero-card">
        <div class="hero-label">Total Net Worth</div>
        <div class="hero-number">${total_nw:,.0f}</div>
        <div class="hero-label">Goal Milestone: {min(total_nw/NW_GOAL*100, 100.0):.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN DASHBOARD ---
c1, c2, c3 = st.columns(3)
with c1: st.metric("Liquid Cash", f"${acc_vals['Checking'] + acc_vals['Savings']:,.0f}")
with c2: st.metric("Investment Value", f"${acc_vals['Retirement']:,.0f}")
with c3: st.metric("Monthly Burn", "$3,420", delta="-12%", delta_color="normal")

st.markdown("---")

tabs = st.tabs(["Dashboard", "Budget", "Spending", "Markets", "Advisor"])

with tabs[0]: # Dashboard
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Savings Momentum")
        # Line Chart for Savings Growth
        chart_data = pd.DataFrame(np.random.randn(20, 1).cumsum(), columns=['Growth'])
        fig = px.line(chart_data, template="plotly_white", color_discrete_sequence=['#0A192F'])
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col_b:
        st.subheader("Advisor Insight")
        st.info("“Your savings goal is safe this month. You can increase groceries by $40 and still stay on track.”")

with tabs[1]: # Budget
    st.subheader("Monthly Plan")
    st.write("Allocation overview...")
    # Placeholder for bar chart
    st.progress(0.65, text="Fixed Costs: 65%")
    st.progress(0.20, text="Savings: 20%")
    st.progress(0.15, text="Flex: 15%")

with tabs[2]: # Spending
    st.subheader("Transaction Log")
    t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    t_amt = st.number_input("Amount", min_value=0.0)
    t_cat = st.selectbox("Category", ["Food", "Invest", "Leisure", "Housing"])
    if st.button("Commit Entry", use_container_width=True):
        st.toast("Entry Secured")

with tabs[3]: # Markets
    st.subheader("Watchlist")
    ticker = st.selectbox("Asset", ["AAPL", "BTC-USD", "TSLA"])
    st.caption("Real-time market data sync enabled.")

with tabs[4]: # Advisor (Assistant)
    st.subheader("Private Advisor")
    st.text_input("Ask about your finances...", placeholder="How much can I spend on a vacation?")
    st.markdown("<p style='font-size:12px; color:gray;'>Aura uses secure analytics to provide financial guidance.</p>", unsafe_allow_html=True)
