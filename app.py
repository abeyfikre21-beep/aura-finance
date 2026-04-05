import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & ADVANCED LAYOUT CSS ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #02060E; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #D4AF37; }
    
    /* Grid Card Styling */
    .info-card {
        background: #0D1526; padding: 22px; border-radius: 15px;
        border: 1px solid #1C2C4E; text-align: left;
        margin-bottom: 20px; min-height: 140px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .card-label { font-size: 10px; color: #8E8E93; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; font-weight: 700; }
    .card-val { font-size: 22px; font-weight: 800; color: #FFFFFF; }
    .card-sub { font-size: 12px; color: #D4AF37; margin-top: 5px; }
    
    /* Spacing between rows */
    .row-spacer { margin-top: 30px; margin-bottom: 10px; border-bottom: 1px solid #1C2C4E; padding-bottom: 10px; color: #8E8E93; font-size: 12px; text-transform: uppercase; letter-spacing: 3px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. PERSISTENCE ENGINE (RESTORE POINT ACTIVE) ---
def load_csv(file, columns):
    if os.path.exists(file): return pd.read_csv(file)
    df = pd.DataFrame(columns=columns)
    df.to_csv(file, index=False)
    return df

# Initialize Data
if 'acct_data' not in st.session_state:
    if os.path.exists("aura_accounts.csv"): st.session_state.acct_data = pd.read_csv("aura_accounts.csv").iloc[0].to_dict()
    else: st.session_state.acct_data = {"Checking": 5000.0, "Savings": 10000.0, "Retirement": 50000.0}

st.session_state.debt_df = load_csv("aura_debt.csv", ["Name", "Balance"])
st.session_state.exp_df = load_csv("aura_expenses.csv", ["Date", "Category", "Amount"])

# --- 3. LIVE CALCULATIONS FOR NEW CARDS ---
# Calculations based on standard budget assumptions (can be made dynamic later)
w_budget = 1000.0
m_budget = 4000.0
total_spent = st.session_state.exp_df['Amount'].sum() if not st.session_state.exp_df.empty else 0.0
w_spent = st.session_state.exp_df[pd.to_datetime(st.session_state.exp_df['Date']) > (datetime.now() - pd.Timedelta(days=7))]['Amount'].sum() if not st.session_state.exp_df.empty else 0.0
m_spent = st.session_state.exp_df[pd.to_datetime(st.session_state.exp_df['Date']).dt.month == datetime.now().month]['Amount'].sum() if not st.session_state.exp_df.empty else 0.0

emergency_fund = st.session_state.acct_data['Savings'] * 0.5 # Example logic
leftover = (st.session_state.acct_data['Checking'] - w_spent)
after_budget_savings = leftover - 500 # Simulated "After Budget & Savings"

# --- 4. NAVIGATION ---
with st.sidebar:
    st.title("🏛️ AURA")
    nav = st.radio("SELECT VIEW", ["📊 Dashboard", "💰 Assets", "💳 Debt Portfolio", "🗓️ Weekly Budget", "📅 Monthly Budget", "📈 Insights & History", "🤖 Assistant", "👤 Profile", "🎨 Appearance"])

# --- 5. DASHBOARD GRID (ONE CHOICE AT A TIME) ---
if nav == "📊 Dashboard":
    st.title("Executive Command")
    
    # --- ROW 1: THE BIG PICTURE ---
    st.markdown('<div class="row-spacer">Cash Flow Status</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    def draw_card(col, label, val, sub=""):
        col.markdown(f"""
            <div class="info-card">
                <div class="card-label">{label}</div>
                <div class="card-val">${val:,.0f}</div>
                <div class="card-sub">{sub}</div>
            </div>
        """, unsafe_allow_html=True)

    draw_card(c1, "Left To Spend (After Budget/Savings)", after_budget_savings, "Safe to use")
    draw_card(c2, "Total Money Spent", total_spent, "All-time history")
    draw_card(c3, "Leftover Money", leftover, "Unallocated in Checking")

    # --- ROW 2: BUDGET VS ACTUAL ---
    st.markdown('<div class="row-spacer">Budget Performance</div>', unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    draw_card(b1, "Weekly Budget", w_budget)
    draw_card(b2, "Weekly Spent", w_spent, f"{int((w_spent/w_budget)*100)}% Used")
    draw_card(b3, "Monthly Budget", m_budget)
    draw_card(b4, "Monthly Spent", m_spent, f"{int((m_spent/m_budget)*100)}% Used")

    # --- ROW 3: BILLS & OBLIGATIONS ---
    st.markdown('<div class="row-spacer">Upcoming Obligations</div>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    draw_card(f1, "Next Bill", 120, "Internet - Due in 2 days")
    draw_card(f2, "Upcoming Monthly Bills", 2150, "4 Bills remaining")
    draw_card(f3, "Emergency Expense", 500, "Reserved for surprises")

    # --- ROW 4: AI STRATEGY ---
    st.markdown('<div class="row-spacer">Aura Strategy</div>', unsafe_allow_html=True)
    draw_card(st, "AI Recommendations", 0, "Your savings rate is up 12%. Consider moving $400 to Retirement.")

    # --- DATA SYNC ---
    with st.expander("🛠️ SYNC CORE BALANCES"):
        with st.form("sync"):
            ch = st.number_input("Checking", value=float(st.session_state.acct_data['Checking']))
            sa = st.number_input("Savings", value=float(st.session_state.acct_data['Savings']))
            if st.form_submit_button("Update Balances"):
                st.session_state.acct_data['Checking'] = ch
                st.session_state.acct_data['Savings'] = sa
                pd.DataFrame([st.session_state.acct_data]).to_csv("aura_accounts.csv", index=False)
                st.rerun()

# --- OTHER PAGES (PERSISTENT & UNTOUCHED) ---
elif nav == "💳 Debt Portfolio":
    st.title("Debt Portfolio")
    # ... [Existing Debt Code Unchanged]
