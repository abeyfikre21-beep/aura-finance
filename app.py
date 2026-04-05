import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
import os
from PIL import Image

# --- 1. LUXURY THEME SETTINGS ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #050505; }
    [data-testid="stMetricValue"] { font-size: 30px !important; font-weight: 800 !important; color: #D4AF37 !important; }
    div[data-testid="stMetric"] { background: rgba(28, 28, 30, 0.6); border: 1px solid rgba(212, 175, 55, 0.2); padding: 15px; border-radius: 15px; }
    .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: black !important; }
    .stProgress > div > div > div > div { background-color: #D4AF37; }
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

# --- 2. DATA & FOLDER SETUP ---
DB_FILE = "aura_vault.csv"
IMG_DIR = "receipts"
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        if 'Receipt' not in df.columns: df['Receipt'] = "None"
        return df
    return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account", "Receipt"])

if 'df' not in st.session_state: st.session_state.df = load_data()

# --- 3. SIDEBAR CONFIGS ---
st.sidebar.title("🎯 Wealth Goals")
NW_GOAL = st.sidebar.number_input("Net Worth Target ($)", value=100000, step=5000)

st.sidebar.title("🛡️ Monthly Budgets")
BUDGETS = {
    "Food": st.sidebar.slider("Food Budget", 0, 2000, 500),
    "Leisure": st.sidebar.slider("Leisure Budget", 0, 2000, 300),
    "Transport": st.sidebar.slider("Transport Budget", 0, 2000, 200),
    "Bills": st.sidebar.slider("Bills Budget", 0, 5000, 1500)
}

st.sidebar.title("📈 Watchlist")
ticker_input = st.sidebar.text_input("Tickers", "AAPL, TSLA, BTC-USD")
tickers = [t.strip().upper() for t in ticker_input.split(",")]

# --- 4. ACCOUNT TOTALS ---
accounts = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
for _, row in st.session_state.df.iterrows():
    val = row['Amount'] if row['Type'] == 'Income' else -row['Amount']
    if row['Account'] in accounts: accounts[row['Account']] += val

total_nw = sum(accounts.values())

# --- 5. EXECUTIVE DASHBOARD ---
st.title("🏛️ Aura Executive")
progress_pct = min(total_nw / NW_GOAL, 1.0)
st.write(f"**Wealth Progress:** ${total_nw:,.0f} / ${NW_GOAL:,.0f}")
st.progress(progress_pct)

c1, c2, c3 = st.columns(3)
c1.metric("Net Worth", f"${total_nw:,.0f}")
c2.metric("Liquid Cash", f"${accounts['Checking'] + accounts['Savings']:,.0f}")
c3.metric("Investments", f"${accounts['Retirement']:,.0f}")

# --- 6. NAVIGATION ---
tabs = st.tabs(["💸 Log", "📊 Stats", "📈 Markets", "🧠 AI", "⚙️"])

with tabs[0]: # LOG TAB
    st.subheader("New Entry")
    t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    t_amt = st.number_input("Amount", min_value=0.0)
    t_cat = st.selectbox("Category", ["Food", "Invest", "Bills", "Leisure", "Housing", "Transport"])
    t_acc = st.selectbox("Account", list(accounts.keys()))
    
    # Live Budget Warning
    if t_type == "Expense" and t_cat in BUDGETS:
        current_month = datetime.now().strftime('%Y-%m')
        spent = st.session_state.df[(st.session_state.df['Category'] == t_cat) & 
                                   (st.session_state.df['Date'].dt.strftime('%Y-%m') == current_month)]['Amount'].sum()
        remaining = BUDGETS[t_cat] - spent
        if remaining > 0:
            st.caption(f"🛡️ Budget Remaining for {t_cat}: **${remaining:,.2f}**")
        else:
            st.error(f"⚠️ Warning: You are **${abs(remaining):,.2f}** over your {t_cat} budget!")

    receipt_file = st.file_uploader("Capture Receipt", type=['jpg', 'png', 'jpeg'])
    
    if st.button("🚀 Commit Transaction", use_container_width=True):
        img_path = "None"
        if receipt_file:
            img_path = f"{IMG_DIR}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            img = Image.open(receipt_file)
            img.save(img_path)
            
        new_row = pd.DataFrame([[pd.to_datetime(datetime.now().date()), t_type, t_cat, t_amt, t_acc, img_path]], 
                               columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.session_state.df.to_csv(DB_FILE, index=False)
        st.rerun()

with tabs[1]: # STATS TAB
    st.subheader("Budget vs. Reality")
    # Budget Chart
    current_month = datetime.now().strftime('%Y-%m')
    actuals = st.session_state.df[st.session_state.df['Date'].dt.strftime('%Y-%m') == current_month].groupby('Category')['Amount'].sum()
    
    compare_data = []
    for cat, limit in BUDGETS.items():
        compare_data.append({"Category": cat, "Type": "Budget", "Amount": limit})
        compare_data.append({"Category": cat, "Type": "Actual", "Amount": actuals.get(cat, 0)})
    
    if compare_data:
        fig_b = px.bar(pd.DataFrame(compare_data), x="Category", y="Amount", color="Type", 
                      barmode="group", template="plotly_dark", color_discrete_map={"Budget": "#1c1c1e", "Actual": "#D4AF37"})
        st.plotly_chart(fig_b, use_container_width=True)

    for i, row in st.session_state.df.sort_index(ascending=False).head(10).iterrows():
        with st.expander(f"{row['Date'].strftime('%m/%d')} - {row['Category']}: ${row['Amount']}"):
            if row['Receipt'] != "None" and os.path.exists(str(row['Receipt'])):
                st.image(row['Receipt'])

with tabs[2]: # MARKETS TAB
    sel = st.selectbox("Select Asset", tickers)
    if sel:
        try:
            hist = yf.download(sel, period="1mo", interval="1d")
            if not hist.empty:
                hist.columns = [col[0] if isinstance(col, tuple) else col for col in hist.columns]
                fig_stock = px.line(hist, y="Close", template="plotly_dark")
                fig_stock.update_traces(line_color='#D4AF37')
                st.plotly_chart(fig_stock, use_container_width=True)
        except: st.error("Market Sync Error")

with tabs[3]: # AI TAB
    st.subheader("🔮 Aura Forecast")
    df = st.session_state.df
    if not df.empty:
        df['Month'] = df['Date'].dt.strftime('%b %Y')
        summary = df.groupby(['Month', 'Type'])['Amount'].sum().unstack(fill_value=0)
        if 'Income' in summary and 'Expense' in summary:
            avg_savings = (summary['Income'] - summary['Expense']).mean()
            if avg_savings > 0:
                months = (NW_GOAL - total_nw) / avg_savings
                st.success(f"💎 **Financial Path:** Hitting ${NW_GOAL:,.0f} in **{months:.1f} months**.")
            else: st.warning("Burn rate exceeds income. Adjust budgets to stay on track.")

with tabs[4]: # SYSTEM
    if st.button("Logout"): 
        st.session_state.auth = False
        st.rerun()
