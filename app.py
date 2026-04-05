import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf
from datetime import datetime
import os
from PIL import Image

# --- 1. SETTINGS ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
    .stApp { background-color: #050505; }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; font-weight: 800 !important; }
    div[data-testid="stMetric"] { background: rgba(28, 28, 30, 0.6); border: 1px solid rgba(212, 175, 55, 0.2); border-radius: 15px; padding: 15px; }
    .stProgress > div > div > div > div { background-color: #D4AF37; }
</style>""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ Aura Secure")
    if st.text_input("Vault PIN", type="password") == "1234":
        st.session_state.auth = True
        st.rerun()
    st.stop()

# --- 2. DATA ---
DB_FILE, IMG_DIR = "aura_vault.csv", "receipts"
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account", "Receipt"])

st.session_state.df = load_data()

# --- 3. SIDEBAR ---
NW_GOAL = st.sidebar.number_input("Goal ($)", value=100000)
BUDGETS = {"Food": st.sidebar.slider("Food", 0, 2000, 500), "Leisure": st.sidebar.slider("Leisure", 0, 2000, 300)}
tickers = [t.strip().upper() for t in st.sidebar.text_input("Watchlist", "AAPL, BTC-USD").split(",")]

# --- 4. CALCS ---
acc_vals = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
for _, r in st.session_state.df.iterrows():
    if pd.notnull(r['Amount']):
        v = r['Amount'] if r['Type'] == 'Income' else -r['Amount']
        if r['Account'] in acc_vals: acc_vals[r['Account']] += v

total_nw = sum(acc_vals.values())

# --- 5. DASHBOARD ---
st.title("🏛️ Aura Executive")
st.progress(min(total_nw / NW_GOAL, 1.0) if NW_GOAL > 0 else 0)
c1, c2, c3 = st.columns(3)
c1.metric("Net Worth", f"${total_nw:,.0f}")
c2.metric("Liquid", f"${acc_vals['Checking'] + acc_vals['Savings']:,.0f}")
c3.metric("Invested", f"${acc_vals['Retirement']:,.0f}")

tabs = st.tabs(["💸 Log", "📊 Stats", "📈 Markets", "🧠 AI"])

with tabs[0]: # LOG
    t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    t_amt = st.number_input("Amount", min_value=0.0)
    t_cat = st.selectbox("Category", ["Food", "Invest", "Bills", "Leisure", "Housing"])
    t_acc = st.selectbox("Account", list(acc_vals.keys()))
    img_file = st.file_uploader("Receipt", type=['jpg', 'png'])
    
    if st.button("🚀 Commit", use_container_width=True):
        path = "None"
        if img_file:
            path = f"{IMG_DIR}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            Image.open(img_file).save(path)
        new = pd.DataFrame([[pd.to_datetime(datetime.now().date()), t_type, t_cat, t_amt, t_acc, path]], columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True)
        st.session_state.df.to_csv(DB_FILE, index=False)
        st.rerun()

with tabs[1]: # STATS
    st.subheader("Budget vs Reality")
    curr_mo = datetime.now().strftime('%Y-%m')
    if not st.session_state.df.empty:
        # FIXED: Complete logic for the bar chart
        df = st.session_state.df
        actuals = df[df['Date'].dt.strftime('%Y-%m') == curr_mo].groupby('Category')['Amount'].sum()
        comp = []
        for cat, lim in BUDGETS.items():
            comp.append({"Cat": cat, "Type": "Budget", "Amt": lim})
            comp.append({"Cat": cat, "Type": "Actual", "Amt": actuals.get(cat, 0)})
        st.plotly_chart(px.bar(pd.DataFrame(comp), x="Cat", y="Amt", color="Type", barmode="group", template="plotly_dark", color_discrete_map={"Budget": "#1c1c1e", "Actual": "#D4AF37"}), use_container_width=True)

with tabs[2]: # MARKETS
    sel = st.selectbox("Ticker", tickers)
    if sel:
        try:
            h = yf.download(sel, period="1mo")
            if not h.empty:
                h.columns = [c[0] if isinstance(c, tuple) else c for c in h.columns]
                st.plotly_chart(px.line(h, y="Close", template="plotly_dark").update_traces(line_color='#D4AF37'), use_container_width=True)
        except: st.error("Market Error")

with tabs[3]: # AI
    df = st.session_state.df
    if not df.empty and 'Income' in df['Type'].values:
        summary = df.groupby([df['Date'].dt.strftime('%b %Y'), 'Type'])['Amount'].sum().unstack(fill_value=0)
        if 'Income' in summary and 'Expense' in summary:
            savings = (summary['Income'] - summary['Expense']).mean()
            if savings > 0:
                st.success(f"💎 Goal reached in **{(NW_GOAL-total_nw)/savings:.1f} months**")
            else: st.warning("Spending exceeds income.")
