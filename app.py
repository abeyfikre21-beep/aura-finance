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
    
    /* Input Styling to look like plain text in a card */
    div[data-testid="stNumberInput"] label { display: none; } /* Hide labels for card-inputs */
    div[data-testid="stNumberInput"] input {
        background-color: transparent !important;
        border: none !important;
        color: white !important;
        font-weight: 900 !important;
        padding: 0 !important;
        text-align: center !important;
    }
    
    /* Hero Card Structure */
    .hero-card {
        background: linear-gradient(145deg, #0D1526, #16223D); 
        padding: 25px 10px; border-radius: 20px;
        border: 1px solid #D4AF37; text-align: center;
        margin-bottom: 15px;
    }
    .hero-label { font-size: 11px; color: #8E8E93; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; margin-bottom: 5px;}
    
    /* Detail Card Structure */
    .detail-card {
        background: #090F1C; padding: 15px; border-radius: 12px;
        border: 1px solid #1C2C4E; text-align: left; margin-bottom: 10px;
    }
    .detail-label { font-size: 9px; color: #6C757D; text-transform: uppercase; font-weight: 600; }
    
    .section-title { margin: 25px 0 10px 0; color: #8E8E93; font-size: 10px; text-transform: uppercase; letter-spacing: 4px; text-align: center;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE (PERSISTENCE) ---
def safe_save(file, data):
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
        st.session_state.targets = {"WeeklyBudget": 1000.0, "MonthlyBudget": 4000.0, "NextBill": 0.0, "Emergency": 500.0, "Leftover": 0.0, "Recommend": 0.0}

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
    st.info("Click any number on the dashboard to edit it instantly.")

# --- 5. DASHBOARD (DIRECT EDIT MODE) ---
if nav == "📊 Dashboard":
    st.markdown('<div class="section-title">Principal Wealth (Click to Edit)</div>', unsafe_allow_html=True)
    
    h_cols = st.columns(5)
    
    # Hero Card 1: Net Worth (Auto-Calculated, not editable)
    with h_cols[0]:
        st.markdown(f'<div class="hero-card"><div class="hero-label">Net Worth</div><div style="font-size:28px; font-weight:900; color:#D4AF37;">${net_worth:,.0f}</div></div>', unsafe_allow_html=True)
    
    # Hero Cards 2-4: Editable
    keys = ["Checking", "Savings", "Retirement"]
    for i, key in enumerate(keys, 1):
        with h_cols[i]:
            st.markdown(f'<div class="hero-card"><div class="hero-label">{key}</div>', unsafe_allow_html=True)
            val = st.number_input(f"edit_{key}", value=float(st.session_state.acct_data[key]), step=100.0, key=f"h_{key}")
            if val != st.session_state.acct_data[key]:
                st.session_state.acct_data[key] = val
                safe_save("aura_accounts.csv", st.session_state.acct_data)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Hero Card 5: Total Debt (Auto-Calculated)
    with h_cols[4]:
        st.markdown(f'<div class="hero-card"><div class="hero-label">Total Debt</div><div style="font-size:28px; font-weight:900; color:#FF5252;">${d_total:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Budgetary Metrics (Click to Edit)</div>', unsafe_allow_html=True)
    
    # Function for Editable Small Cards
    def editable_detail(col, label, current_val, storage_key):
        with col:
            st.markdown(f'<div class="detail-card"><div class="detail-label">{label}</div>', unsafe_allow_html=True)
            new_val = st.number_input(f"edit_{storage_key}", value=float(current_val), step=10.0, key=f"d_{storage_key}")
            if new_val != current_val:
                st.session_state.targets[storage_key] = new_val
                safe_save("aura_targets.csv", st.session_state.targets)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Row 1 of Details
    d_r1 = st.columns(4)
    editable_detail(d_row1[0], "Weekly Budget", st.session_state.targets["WeeklyBudget"], "WeeklyBudget")
    # Total Spent is Live-calculated, so we just display it
    with d_row1[1]:
        st.markdown(f'<div class="detail-card"><div class="detail-label">Total Spent</div><div style="font-size:17px; font-weight:700;">${total_spent:,.0f}</div></div>', unsafe_allow_html=True)
    editable_detail(d_row1[2], "Monthly Budget", st.session_state.targets["MonthlyBudget"], "MonthlyBudget")
    editable_detail(d_row1[3], "Next Bill", st.session_state.targets["NextBill"], "NextBill")

    # Row 2 of Details
    d_r2 = st.columns(4)
    editable_detail(d_row2[0], "Emergency Reserve", st.session_state.targets["Emergency"], "Emergency")
    editable_detail(d_row2[1], "Leftover Money", st.session_state.targets["Leftover"], "Leftover")
    editable_detail(d_row2[2], "Recommendations", st.session_state.targets["Recommend"], "Recommend")
    with d_row2[3]:
        st.markdown(f'<div class="detail-card"><div class="detail-label">Next Step</div><div style="font-size:12px; font-weight:700; color:#D4AF37;">Review Debt</div></div>', unsafe_allow_html=True)

# --- DEBT PORTFOLIO PRESERVED ---
elif nav == "💳 Debt Portfolio":
    st.title("Debt Portfolio")
    # Existing debt code remains...
