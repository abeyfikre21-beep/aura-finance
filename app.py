import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
import os

# --- 1. LUXURY THEME SETTINGS ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #050505; }
    [data-testid="stMetricValue"] { font-size: 30px !important; font-weight: 800 !important; color: #D4AF37 !important; }
    div[data-testid="stMetric"] { background: rgba(28, 28, 30, 0.6); border: 1px solid rgba(212, 175, 55, 0.2); padding: 15px; border-radius: 15px; }
    .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

USER_PIN = "1234"

if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ Aura Secure")
    pin = st.text_input("Vault PIN", type="password")
    if st.button("Unlock Access"):
        if pin == USER_PIN:
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- 2. DATA VAULT ---
DB_FILE = "aura_vault.csv"
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account"])

if 'df' not in st.session_state: st.session_state.df = load_data()

# --- 3. MARKET ENGINE ---
st.sidebar.title("📈 Watchlist")
ticker_input = st.sidebar.text_input("Tickers", "AAPL, TSLA, BTC-USD")
tickers = [t.strip().upper() for t in ticker_input.split(",")]

# --- 4. ACCOUNT TOTALS ---
accounts = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
for _, row in st.session_state.df.iterrows():
    val = row['Amount'] if row['Type'] == 'Income' else -row['Amount']
    if row['Account'] in accounts: accounts[row['Account']] += val

# --- 5. DASHBOARD ---
st.title("🏛️ Aura Executive")
c1, c2, c3 = st.columns(3)
c1.metric("Net Worth", f"${sum(accounts.values()):,.0f}")
c2.metric("Liquid Cash", f"${accounts['Checking'] + accounts['Savings']:,.0f}")
c3.metric("Investments", f"${accounts['Retirement']:,.0f}")

# --- 6. NAVIGATION ---
tabs = st.tabs(["💸 Log", "📊 Stats", "📈 Markets", "⚙️"])

with tabs[0]:
    t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    t_amt = st.number_input("Amount", min_value=0.0)
    t_cat = st.selectbox("Category", ["Food", "Invest", "Bills", "Leisure", "Housing"])
    t_acc = st.selectbox("Account", list(accounts.keys()))
    if st.button("🚀 Commit Transaction", use_container_width=True):
        new_row = pd.DataFrame([[pd.to_datetime(datetime.now().date()), t_type, t_cat, t_amt, t_acc]], columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.session_state.df.to_csv(DB_FILE, index=False)
        st.rerun()

with tabs[1]:
    exp_df = st.session_state.df[st.session_state.df['Type']=='Expense']
    if not exp_df.empty:
        # FIXED: Color codes are now fully terminated
        fig = px.pie(exp_df, values='Amount', names='Category', hole=0.7, 
                     color_discrete_sequence=['#D4AF37', '#1c1c1e', '#C0C0C0'])
        fig.update_layout(showlegend=False, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(st.session_state.df.sort_index(ascending=False), use_container_width=True)

with tabs[2]:
    sel = st.selectbox("Select Asset", tickers)
    if sel:
        try:
            hist = yf.download(sel, period="1mo", interval="1d")
            if not hist.empty:
                # Clean column headers
                hist.columns = [col[0] if isinstance(col, tuple) else col for col in hist.columns]
                fig_stock = px.line(hist, y="Close", title=f"{sel} (30D)", template="plotly_dark")
                fig_stock.update_traces(line_color='#D4AF37')
                st.plotly_chart(fig_stock, use_container_width=True)
            else:
                st.warning(f"No data found for {sel}.")
        except Exception as e:
            st.error(f"Market Error: {e}")
