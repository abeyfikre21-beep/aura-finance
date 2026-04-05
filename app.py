import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf
from datetime import datetime
import os

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #F9F7F5 !important; color: #1A1A1A !important; }
    header { visibility: hidden !important; }
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #0A192F !important; }
    p, span, label { font-family: 'Inter', sans-serif !important; }
    .hero-card {
        background: #0A192F; color: white !important; padding: 40px;
        border-radius: 24px; text-align: center; margin-bottom: 25px;
    }
    .hero-label { font-size: 13px; opacity: 0.8; text-transform: uppercase; letter-spacing: 1.5px; color: white !important; }
    .hero-number { font-size: 56px; font-family: 'Playfair Display', serif; margin: 10px 0; color: white !important; }
    div[data-testid="stMetric"] {
        background: white !important; border: 1px solid #E5E1DA !important;
        border-radius: 16px !important; padding: 20px !important;
    }
    [data-testid="stMetricValue"] { color: #0A192F !important; font-size: 32px !important; font-weight: 700 !important; }
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

# --- 3. SIDEBAR ---
st.sidebar.title("🏛️ Aura Control")
NW_GOAL = st.sidebar.number_input("Wealth Goal", value=100000)

if st.sidebar.button("✨ Load Demo Data"):
    demo_data = pd.DataFrame([
        [pd.to_datetime('2026-04-01'), 'Income', 'Salary', 8500, 'Checking'],
        [pd.to_datetime('2026-04-02'), 'Expense', 'Housing', 3200, 'Checking'],
        [pd.to_datetime('2026-04-03'), 'Expense', 'Food', 150, 'Checking'],
        [pd.to_datetime('2026-04-04'), 'Expense', 'Leisure', 200, 'Savings']
    ], columns=["Date", "Type", "Category", "Amount", "Account"])
    st.session_state.df = demo_data
    st.rerun()

if st.sidebar.button("🗑️ Clear All Data"):
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.df = pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account"])
    st.rerun()

# --- 4. CALCS ---
acc_vals = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
for _, r in st.session_state.df.iterrows():
    val = r['Amount'] if r['Type'] == 'Income' else -r['Amount']
    if r['Account'] in acc_vals: acc_vals[r['Account']] += val
total_nw = sum(acc_vals.values())

# --- 5. MAIN UI ---
st.markdown(f"""<div class="hero-card"><div class="hero-label">Total Net Worth</div>
    <div class="hero-number">${total_nw:,.0f}</div>
    <div class="hero-label">Goal Milestone: {min(total_nw/NW_GOAL*100, 100.0):.1f}%</div></div>""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("Cash Reserves", f"${acc_vals['Checking'] + acc_vals['Savings']:,.0f}")
c2.metric("Investments", f"${acc_vals['Retirement']:,.0f}")
c3.metric("Liabilities", f"${abs(acc_vals['Debt']):,.0f}")

tabs = st.tabs(["🏛️ Home", "💸 Transactions", "📊 Strategy", "🧠 Advisor"])

with tabs[0]:
    st.subheader("Performance Trend")
    chart_data = pd.DataFrame(np.random.randn(15, 1).cumsum() + 100, columns=['Value'])
    st.plotly_chart(px.line(chart_data, template="plotly_white", color_discrete_sequence=['#0A192F']).update_layout(height=300), use_container_width=True)

with tabs[1]:
    st.subheader("Log Wealth Event")
    col1, col2 = st.columns(2)
    t_type = col1.radio("Type", ["Expense", "Income"], horizontal=True)
    t_amt = col2.number_input("Amount", min_value=0.0)
    t_cat = st.selectbox("Category", ["Food", "Invest", "Bills", "Leisure", "Housing"])
    t_acc = st.selectbox("Account", list(acc_vals.keys()))
    if st.button("🚀 Secure Entry", use_container_width=True):
        new_row = pd.DataFrame([[pd.to_datetime(datetime.now().date()), t_type, t_cat, t_amt, t_acc]], columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.session_state.df.to_csv(DB_FILE, index=False)
        st.success("Entry Secured")
        st.rerun()

with tabs[2]:
    st.subheader("Monthly Strategy")
    if st.session_state.df.empty:
        st.info("Log a transaction to view strategy analytics.")
    else:
        curr_mo = datetime.now().strftime('%Y-%m')
        df = st.session_state.df
        mask = df['Date'].dt.strftime('%Y-%m') == curr_mo
        if mask.any():
            fig = px.pie(df[mask], values='Amount', names='Category', hole=0.6, template="plotly_white", color_discrete_sequence=['#0A192F', '#2D5A27', '#E5E1DA', '#666666'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No data for this month yet.")

with tabs[3]:
    st.subheader("Aura Intelligence")
    st.text_input("Consult with your advisor...", placeholder="How is my savings rate looking?")
    if st.session_state.df.empty:
        st.write("Advisor is awaiting data to begin analysis.")
    else:
        st.write("✨ *Analysis: Your primary burn rate is in Housing. Reducing Leisure by 10% would accelerate your goal by 2 months.*")
