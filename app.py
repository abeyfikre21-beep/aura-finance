import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #02060E; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #D4AF37; }
    .hero-card {
        background: #0D1526; padding: 20px; border-radius: 15px;
        border: 1px solid #1C2C4E; text-align: center;
    }
    .hero-label { font-size: 11px; color: #8E8E93; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px;}
    .hero-val { font-size: 24px; font-weight: 800; color: #FFFFFF; }
    .budget-card {
        background: #0D1526; padding: 18px; border-radius: 12px;
        border: 1px solid #1C2C4E; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE SAVING ENGINE (PERSISTENCE LAYER) ---
def load_csv(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    df = pd.DataFrame(columns=columns)
    df.to_csv(file, index=False)
    return df

# Initialize Session State from Files (This prevents data loss)
if 'acct_data' not in st.session_state:
    if os.path.exists("aura_accounts.csv"):
        st.session_state.acct_data = pd.read_csv("aura_accounts.csv").iloc[0].to_dict()
    else:
        st.session_state.acct_data = {"Checking": 0.0, "Savings": 0.0, "Retirement": 0.0}

if 'debt_df' not in st.session_state:
    st.session_state.debt_df = load_csv("aura_debt.csv", ["Name", "Balance"])

if 'exp_df' not in st.session_state:
    st.session_state.exp_df = load_csv("aura_expenses.csv", ["Date", "Category", "Amount"])

# --- 3. GLOBAL CALCULATIONS ---
d_total = float(st.session_state.debt_df['Balance'].sum()) if not st.session_state.debt_df.empty else 0.0
a_total = sum(st.session_state.acct_data.values())
current_nw = a_total - d_total

# --- 4. SIDEBAR NAVIGATION (RESTORED) ---
with st.sidebar:
    st.title("🏛️ AURA")
    nav = st.radio("SELECT VIEW", [
        "📊 Dashboard", 
        "💰 Assets (Wealth)", 
        "💳 Debt Portfolio",  # <--- Back in the menu
        "🗓️ Weekly Budget", 
        "📅 Monthly Budget",
        "📈 Insights & History",
        "🤖 Assistant",
        "🎨 Settings"
    ])

# --- 5. PAGE LOGIC ---

if nav == "📊 Dashboard":
    st.title("Executive Dashboard")
    h1, h2, h3, h4, h5 = st.columns(5)
    
    def draw_c(col, l, v, c="#FFFFFF"):
        col.markdown(f'<div class="hero-card"><div class="hero-label">{l}</div><div class="hero-val" style="color:{c}">${v:,.0f}</div></div>', unsafe_allow_html=True)

    draw_c(h1, "Net Worth", current_nw, "#D4AF37")
    draw_c(h2, "Checking", st.session_state.acct_data['Checking'])
    draw_c(h3, "Savings", st.session_state.acct_data['Savings'])
    draw_c(h4, "Retirement", st.session_state.acct_data['Retirement'])
    draw_c(h5, "Total Debt", d_total, "#FF5252")

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🛠️ QUICK ADJUST BALANCES"):
        with st.form("hero_edit"):
            c1, c2, c3 = st.columns(3)
            nc = c1.number_input("Checking", value=float(st.session_state.acct_data['Checking']))
            ns = c2.number_input("Savings", value=float(st.session_state.acct_data['Savings']))
            nr = c3.number_input("Retirement", value=float(st.session_state.acct_data['Retirement']))
            if st.form_submit_button("Update All"):
                st.session_state.acct_data = {"Checking": nc, "Savings": ns, "Retirement": nr}
                pd.DataFrame([st.session_state.acct_data]).to_csv("aura_accounts.csv", index=False)
                st.rerun()

elif nav == "💰 Assets (Wealth)":
    st.title("Asset Management")
    st.write(f"Your total liquid and invested assets: **${a_total:,.2f}**")
    st.info("Use the Dashboard 'Quick Adjust' to modify these primary balances.")

elif nav == "💳 Debt Portfolio":
    st.title("Debt Portfolio")
    with st.form("debt_add", clear_on_submit=True):
        dn = st.text_input("Lender Name")
        db = st.number_input("Balance", min_value=0.0)
        if st.form_submit_button("Add Debt"):
            new_row = pd.DataFrame([{"Name": dn, "Balance": db}])
            st.session_state.debt_df = pd.concat([st.session_state.debt_df, new_row], ignore_index=True)
            st.session_state.debt_df.to_csv("aura_debt.csv", index=False) # SAVE TO FILE
            st.rerun()

    st.markdown("### Active Liabilities")
    for i, r in st.session_state.debt_df.iterrows():
        col1, col2 = st.columns([4, 1])
        col1.markdown(f'<div class="budget-card"><b>{r["Name"]}</b>: ${r["Balance"]:,.0f}</div>', unsafe_allow_html=True)
        if col2.button("🗑️", key=f"del_{i}"):
            st.session_state.debt_df = st.session_state.debt_df.drop(i)
            st.session_state.debt_df.to_csv("aura_debt.csv", index=False) # SAVE TO FILE
            st.rerun()

elif nav == "🗓️ Weekly Budget" or nav == "📅 Monthly Budget":
    st.title(nav)
    with st.form("exp_log", clear_on_submit=True):
        cat = st.selectbox("Category", ["Rent", "Groceries", "Savings Goal", "Other"])
        amt = st.number_input("Amount Spent", min_value=0.0)
        if st.form_submit_button("Log Transaction"):
            new_e = pd.DataFrame([{"Date": datetime.now(), "Category": cat, "Amount": amt}])
            st.session_state.exp_df = pd.concat([st.session_state.exp_df, new_e], ignore_index=True)
            st.session_state.exp_df.to_csv("aura_expenses.csv", index=False) # SAVE TO FILE
            st.rerun()

elif nav == "📈 Insights & History":
    st.title("Transaction History")
    st.dataframe(st.session_state.exp_df, use_container_width=True)

elif nav == "🤖 Assistant":
    st.title("Aura Assistant")
    st.chat_input("Ask me anything about your finances...")

elif nav == "🎨 Settings":
    st.title("System Settings")
    if st.button("🔴 Reset All Data"):
        for f in ["aura_accounts.csv", "aura_debt.csv", "aura_expenses.csv"]:
            if os.path.exists(f): os.remove(f)
        st.rerun()
