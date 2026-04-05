import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf
from datetime import datetime
import os
from PIL import Image

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")

# --- 2. THE "QUIET LUXURY" STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #F9F7F5 !important; color: #1A1A1A !important; }
    header { visibility: hidden !important; }
    
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #0A192F !important; }
    p, span, label { font-family: 'Inter', sans-serif !important; color: #1A1A1A !important; }

    .hero-card {
        background: #0A192F;
        color: white !important;
        padding: 40px;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(10, 25, 47, 0.1);
    }
    .hero-label { font-size: 13px; opacity: 0.8; text-transform: uppercase; letter-spacing: 1.5px; color: white !important; }
    .hero-number { font-size: 56px; font-family: 'Playfair Display', serif; margin: 10px 0; color: white !important; }

    div[data-testid="stMetric"] {
        background: white !important;
        border: 1px solid #E5E1DA !important;
        border-radius: 16px !important;
        padding: 20px !important;
    }
    [data-testid="stMetricValue"] { color: #0A192F !important; font-size: 32px !important; font-weight: 700 !important; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent !important; color: #666 !important; font-weight: 600 !important; }
    .stTabs [aria-selected="true"] { color: #0A192F !important; border-bottom: 2px solid #0A192F !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA ENGINE ---
DB_FILE, IMG_DIR = "aura_vault.csv", "receipts"
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account", "Receipt"])

if 'df' not in st.session_state: st.session_state.df = load_data()

# --- 4. SIDEBAR (GOALS & BUDGETS) ---
st.sidebar.title("🎯 Wealth Strategy")
NW_GOAL = st.sidebar.number_input("Net Worth Goal ($)", value=100000)

st.sidebar.title("🛡️ Monthly Guardrails")
BUDGETS = {
    "Food": st.sidebar.slider("Food", 0, 2000, 500),
    "Leisure": st.sidebar.slider("Leisure", 0, 2000, 300),
    "Bills": st.sidebar.slider("Bills", 0, 5000, 1500)
}

st.sidebar.title("📈 Watchlist")
tickers = [t.strip().upper() for t in st.sidebar.text_input("Assets", "AAPL, BTC-USD").split(",")]

# --- 5. CALCULATIONS ---
acc_vals = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
for _, r in st.session_state.df.iterrows():
    if pd.notnull(r['Amount']):
        val = r['Amount'] if r['Type'] == 'Income' else -r['Amount']
        if r['Account'] in acc_vals: acc_vals[r['Account']] += val

total_nw = sum(acc_vals.values())

# --- 6. AUTH GATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<div style='text-align:center; padding-top:100px;'><h1>🏛️ Aura</h1></div>", unsafe_allow_html=True)
    if st.text_input("Security PIN", type="password") == "1234":
        st.session_state.auth = True
        st.rerun()
    st.stop()

# --- 7. MAIN INTERFACE ---
# HERO SECTION
st.markdown(f"""
    <div class="hero-card">
        <div class="hero-label">Total Net Worth</div>
        <div class="hero-number">${total_nw:,.0f}</div>
        <div class="hero-label">Goal Milestone: {min(total_nw/NW_GOAL*100, 100.0):.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("Cash Reserves", f"${acc_vals['Checking'] + acc_vals['Savings']:,.0f}")
c2.metric("Investments", f"${acc_vals['Retirement']:,.0f}")
c3.metric("Liabilities", f"${abs(acc_vals['Debt']):,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

tabs = st.tabs(["🏛️ Home", "💸 Transactions", "📊 Strategy", "📈 Markets", "🧠 Advisor"])

with tabs[0]: # HOME
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.subheader("Asset Performance")
        chart_data = pd.DataFrame(np.random.randn(15, 1).cumsum() + 100, columns=['Value'])
        st.plotly_chart(px.line(chart_data, template="plotly_white", color_discrete_sequence=['#0A192F']).update_layout(height=300), use_container_width=True)
    with col_r:
        st.subheader("Private Insights")
        st.info("“Your savings goal is safe this month. You're on track to hit your milestone early.”")
        if total_nw > NW_GOAL: st.balloons()

with tabs[1]: # TRANSACTIONS (LOGGING)
    st.subheader("Log Wealth Event")
    t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    t_amt = st.number_input("Amount", min_value=0.0)
    t_cat = st.selectbox("Category", ["Food", "Invest", "Bills", "Leisure", "Housing", "Transport"])
    t_acc = st.selectbox("Account", list(acc_vals.keys()))
    
    # Budget Guardrail
    if t_type == "Expense" and t_cat in BUDGETS:
        curr_mo = datetime.now().strftime('%Y-%m')
        spent = st.session_state.df[(st.session_state.df['Category'] == t_cat) & (st.session_state.df['Date'].dt.strftime('%Y-%m') == curr_mo)]['Amount'].sum()
        rem = BUDGETS[t_cat] - spent
        st.caption(f"🛡️ {t_cat} Remaining: ${max(rem, 0):,.2f}")
        if rem <= 0: st.warning(f"Limit reached for {t_cat}")

    if st.button("🚀 Secure Entry", use_container_width=True):
        new_row = pd.DataFrame([[pd.to_datetime(datetime.now().date()), t_type, t_cat, t_amt, t_acc, "None"]], columns=st.session_state.df.columns)
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.session_state.df.to_csv(DB_FILE, index=False)
        st.rerun()

with tabs[2]: # STRATEGY (STATS)
    st.subheader("Budget vs. Actual")
    curr_mo = datetime.now().strftime('%Y-%m')
    actuals = st.session_state.df[st.session_state.df['Date'].dt.strftime('%Y-%m') == curr_mo].groupby('Category')['Amount'].sum()
    comp = []
    for cat, lim in BUDGETS.items():
        comp.append({"Category": cat, "Type": "Plan", "Amt": lim})
        comp.append({"Category": cat, "Type": "Actual", "Amt": actuals.get(cat, 0)})
    if comp:
        st.plotly_chart(px.bar(pd.DataFrame(comp), x="Category", y="Amt", color="Type", barmode="group", template="plotly_white", color_discrete_map={"Plan": "#E5E1DA", "Actual": "#0A192F"}), use_container_width=True)

with tabs[3]: # MARKETS
    sel = st.selectbox("Asset Search", tickers)
    if sel:
        try:
            h = yf.download(sel, period="1mo")
            if not h.empty:
                h.columns = [c[0] if isinstance(c, tuple) else c for c in h.columns]
                st.plotly_chart(px.line(h, y="Close", template="plotly_white").update_traces(line_color='#0A192F'), use_container_width=True)
        except: st.error("Market Sync Offline")

with tabs[4]: # ADVISOR (FORECAST)
    st.subheader("Aura Intelligence")
    df = st.session_state.df
    if not df.empty and 'Income' in df['Type'].values:
        df['MonthYear'] = df['Date'].dt.strftime('%b %Y')
        sum_df = df.groupby(['MonthYear', 'Type'])['Amount'].sum().unstack(fill_value=0)
        if 'Income' in sum_df and 'Expense' in sum_df:
            avg_s = (sum_df['Income'] - sum_df['Expense']).mean()
            if avg_s > 0:
                st.success(f"💎 Forecast: Goal hit in **{(NW_GOAL-total_nw)/avg_s:.1f} months**.")
            else: st.warning("Burn rate exceeds income. Review Strategy tab.")
    st.text_input("Ask Advisor...", placeholder="How can I optimize my portfolio?")
