import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf
from datetime import datetime
import os

# --- 1. DARK MODE LUXURY CSS ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #050505; color: #FFFFFF; }
    
    /* Metrics Styling */
    div[data-testid="stMetric"] {
        background: rgba(28, 28, 30, 0.8);
        border: 1px solid rgba(212, 175, 55, 0.3);
        padding: 20px;
        border-radius: 15px;
    }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; font-size: 36px !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] { color: #8E8E93 !important; font-size: 14px !important; text-transform: uppercase; }

    /* Hero Section */
    .hero-container {
        background: linear-gradient(145deg, #1c1c1e, #050505);
        border: 1px solid rgba(212, 175, 55, 0.2);
        padding: 50px;
        border-radius: 30px;
        text-align: center;
        margin-bottom: 30px;
    }
    .hero-title { color: #8E8E93; font-size: 14px; letter-spacing: 3px; text-transform: uppercase; }
    .hero-amount { color: #D4AF37; font-size: 64px; font-weight: 900; margin: 15px 0; }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 30px; }
    .stTabs [data-baseweb="tab"] { color: #8E8E93 !important; font-weight: 600 !important; }
    .stTabs [aria-selected="true"] { color: #D4AF37 !important; border-bottom: 2px solid #D4AF37 !important; }
    
    /* Input & Sidebar */
    .stNumberInput input, .stSelectbox div { background-color: #1c1c1e !important; color: white !important; border: 1px solid #3a3a3c !important; }
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

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.title("🏛️ Executive Vault")
NW_GOAL = st.sidebar.number_input("Net Worth Goal", value=100000)

if st.sidebar.button("✨ Load Demo Data"):
    demo_data = pd.DataFrame([
        [pd.to_datetime('2026-04-01'), 'Income', 'Salary', 8500, 'Checking'],
        [pd.to_datetime('2026-04-02'), 'Expense', 'Housing', 3200, 'Checking'],
        [pd.to_datetime('2026-04-03'), 'Expense', 'Food', 150, 'Checking'],
        [pd.to_datetime('2026-04-04'), 'Expense', 'Leisure', 200, 'Savings']
    ], columns=["Date", "Type", "Category", "Amount", "Account"])
    st.session_state.df = demo_data
    st.rerun()

# --- 4. CALCULATIONS ---
acc_vals = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
for _, r in st.session_state.df.iterrows():
    val = r['Amount'] if r['Type'] == 'Income' else -r['Amount']
    if r['Account'] in acc_vals: acc_vals[r['Account']] += val
total_nw = sum(acc_vals.values())

# --- 5. INTERFACE ---
st.markdown(f"""
    <div class="hero-container">
        <div class="hero-title">Total Net Worth</div>
        <div class="hero-amount">${total_nw:,.0f}</div>
        <div class="hero-title">Milestone: {min(total_nw/NW_GOAL*100, 100.0):.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("Cash Reserves", f"${acc_vals['Checking'] + acc_vals['Savings']:,.0f}")
c2.metric("Investments", f"${acc_vals['Retirement']:,.0f}")
c3.metric("Liabilities", f"${abs(acc_vals['Debt']):,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

tabs = st.tabs(["🏛️ Terminal", "💸 Transactions", "📊 Analysis", "📈 Markets"])

with tabs[0]: # TERMINAL
    st.subheader("Performance History")
    chart_data = pd.DataFrame(np.random.randn(20, 1).cumsum() + 100, columns=['Value'])
    fig = px.line(chart_data, template="plotly_dark", color_discrete_sequence=['#D4AF37'])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]: # TRANSACTIONS
    st.subheader("Add Transaction")
    col1, col2 = st.columns(2)
    t_type = col1.radio("Type", ["Expense", "Income"], horizontal=True)
    t_amt = col2.number_input("Amount", min_value=0.0)
    t_cat = st.selectbox("Category", ["Food", "Invest", "Bills", "Leisure", "Housing"])
    t_acc = st.selectbox("Account", list(acc_vals.keys()))
    if st.button("🚀 Commit to Vault", use_container_width=True):
        new_row = pd.DataFrame([[pd.to_datetime(datetime.now().date()), t_type, t_cat, t_amt, t_acc]], columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.session_state.df.to_csv(DB_FILE, index=False)
        st.rerun()

with tabs[2]: # ANALYSIS
    st.subheader("Spending Structure")
    if not st.session_state.df.empty:
        fig = px.pie(st.session_state.df, values='Amount', names='Category', hole=0.5, 
                     template="plotly_dark", color_discrete_sequence=['#D4AF37', '#1c1c1e', '#8E8E93'])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Vault empty. Load Demo Data in sidebar to see analysis.")

with tabs[3]: # MARKETS
    ticker = st.text_input("Symbol", "BTC-USD")
    if ticker:
        try:
            data = yf.download(ticker, period="1mo")
            if not data.empty:
                # Fix for multi-index columns in newer yfinance versions
                data.columns = [c[0] if isinstance(c, tuple) else c for c in data.columns]
                fig_m = px.line(data, y="Close", template="plotly_dark")
                fig_m.update_traces(line_color='#D4AF37')
                st.plotly_chart(fig_m, use_container_width=True)
        except: st.error("Market Link Failed")
