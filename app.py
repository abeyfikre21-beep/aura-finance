import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & SEAMLESS INPUT CSS ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #02060E; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #D4AF37; }
    
    /* Makes Number Inputs look like plain text inside the cards */
    div[data-testid="stNumberInput"] label { display: none !important; }
    div[data-testid="stNumberInput"] div[data-baseweb="input"] {
        background-color: transparent !important;
        border: none !important;
    }
    div[data-testid="stNumberInput"] input {
        background-color: transparent !important;
        color: white !important;
        font-weight: 800 !important;
        font-size: 24px !important;
        text-align: center !important;
        border: none !important;
        padding: 0 !important;
    }
    
    /* Style for the smaller cards inputs */
    .small-input div[data-testid="stNumberInput"] input {
        font-size: 16px !important;
        text-align: left !important;
    }

    .hero-card {
        background: linear-gradient(145deg, #0D1526, #16223D); 
        padding: 20px 10px; border-radius: 20px;
        border: 1px solid #D4AF37; text-align: center;
    }
    .detail-card {
        background: #090F1C; padding: 15px; border-radius: 12px;
        border: 1px solid #1C2C4E; margin-bottom: 10px;
    }
    .card-label { font-size: 10px; color: #8E8E93; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; margin-bottom: 8px;}
    .section-title { margin: 30px 0 15px 0; color: #8E8E93; font-size: 10px; text-transform: uppercase; letter-spacing: 4px; text-align: center;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
def save_val(file, data):
    pd.DataFrame([data]).to_csv(file, index=False)

if 'acct_data' not in st.session_state:
    if os.path.exists("aura_accounts.csv"):
        st.session_state.acct_data = pd.read_csv("aura_accounts.csv").iloc[0].to_dict()
    else:
        st.session_state.acct_data = {"Checking": 0.0, "Savings": 0.0, "Retirement": 0.0}

if 'targets' not in st.session_state:
    if os.path.exists("aura_targets.csv"):
        st.session_state.targets = pd.read_csv("aura_targets.csv").iloc[0].to_dict()
    else:
        st.session_state.targets = {"WeeklyBudget": 1000.0, "MonthlyBudget": 4000.0, "NextBill": 0.0, "Emergency": 0.0, "Leftover": 0.0}

st.session_state.debt_df = pd.read_csv("aura_debt.csv") if os.path.exists("aura_debt.csv") else pd.DataFrame(columns=["Name", "Balance"])
st.session_state.exp_df = pd.read_csv("aura_expenses.csv") if os.path.exists("aura_expenses.csv") else pd.DataFrame(columns=["Date", "Category", "Amount"])

# --- 3. LIVE CALCULATIONS ---
d_total = float(st.session_state.debt_df['Balance'].sum())
a_total = sum(st.session_state.acct_data.values())
net_worth = a_total - d_total
total_spent = st.session_state.exp_df['Amount'].sum() if not st.session_state.exp_df.empty else 0.0

# --- 4. NAVIGATION ---
with st.sidebar:
    st.title("🏛️ AURA")
    nav = st.radio("SELECT VIEW", ["📊 Dashboard", "💰 Assets", "💳 Debt Portfolio", "🗓️ Weekly Budget", "📅 Monthly Budget", "📈 Insights", "👤 Profile"])

# --- 5. DASHBOARD ---
if nav == "📊 Dashboard":
    st.markdown('<div class="section-title">Principal Wealth (Click Amount to Edit)</div>', unsafe_allow_html=True)
    h_cols = st.columns(5)
    
    # Card 1: Net Worth (Auto)
    h_cols[0].markdown(f'<div class="hero-card"><div class="card-label">Net Worth</div><div style="font-size:24px; font-weight:900; color:#D4AF37; margin-bottom:15px;">${net_worth:,.0f}</div></div>', unsafe_allow_html=True)
    
    # Cards 2-4: Editable
    for i, key in enumerate(["Checking", "Savings", "Retirement"], 1):
        with h_cols[i]:
            st.markdown(f'<div class="hero-card"><div class="card-label">{key}</div>', unsafe_allow_html=True)
            val = st.number_input(f"edit_{key}", value=float(st.session_state.acct_data[key]), key=f"h_{key}")
            if val != st.session_state.acct_data[key]:
                st.session_state.acct_data[key] = val
                save_val("aura_accounts.csv", st.session_state.acct_data)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Card 5: Debt (Auto)
    h_cols[4].markdown(f'<div class="hero-card"><div class="card-label">Total Debt</div><div style="font-size:24px; font-weight:900; color:#FF5252; margin-bottom:15px;">${d_total:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Budget Metrics</div>', unsafe_allow_html=True)
    
    # Row 1 of Details
    dr1 = st.columns(4)
    
    # Function for consistent smaller editable cards
    def draw_edit_small(col, label, key):
        with col:
            st.markdown(f'<div class="detail-card small-input"><div class="card-label">{label}</div>', unsafe_allow_html=True)
            v = st.number_input(f"edit_t_{key}", value=float(st.session_state.targets[key]), key=f"t_{key}")
            if v != st.session_state.targets[key]:
                st.session_state.targets[key] = v
                save_val("aura_targets.csv", st.session_state.targets)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    draw_edit_small(dr1[0], "Weekly Budget", "WeeklyBudget")
    with dr1[1]:
        st.markdown(f'<div class="detail-card"><div class="card-label">Total Spent</div><div style="font-size:18px; font-weight:700;">${total_spent:,.0f}</div></div>', unsafe_allow_html=True)
    draw_edit_small(dr1[2], "Monthly Budget", "MonthlyBudget")
    draw_edit_small(dr1[3], "Next Bill", "NextBill")

    # Row 2 of Details
    dr2 = st.columns(4)
    draw_edit_small(dr2[0], "Emergency Fund", "Emergency")
    draw_edit_small(dr2[1], "Leftover Money", "Leftover")
    
    with dr2[2]:
        st.markdown(f'<div class="detail-card"><div class="card-label">Recommendations</div><div style="font-size:18px; font-weight:700; color:#D4AF37;">0</div></div>', unsafe_allow_html=True)
    with dr2[3]:
        st.markdown(f'<div class="detail-card"><div class="card-label">System Status</div><div style="font-size:14px; font-weight:700;">Live & Synced</div></div>', unsafe_allow_html=True)

# --- 6. DEBT PORTFOLIO (PRESERVED) ---
elif nav == "💳 Debt Portfolio":
    st.title("Debt Portfolio")
    with st.form("debt_add", clear_on_submit=True):
        n = st.text_input("Lender")
        b = st.number_input("Balance", min_value=0.0)
        if st.form_submit_button("Add Debt"):
            new_df = pd.DataFrame([{"Name": n, "Balance": b}])
            st.session_state.debt_df = pd.concat([st.session_state.debt_df, new_df], ignore_index=True)
            st.session_state.debt_df.to_csv("aura_debt.csv", index=False)
            st.rerun()
