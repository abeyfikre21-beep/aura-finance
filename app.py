import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

# --- 1. SETTINGS & HIGH-CONTRAST DARK THEME ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    
    /* Base Background */
    .stApp { background-color: #050A18; color: #FFFFFF; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #02060E !important; border-right: 1px solid #D4AF37; }
    
    /* Typography */
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #D4AF37 !important; }
    p, span, label, .stMarkdown { font-family: 'Inter', sans-serif !important; color: #E0E0E0 !important; }

    /* Dashboard Cards - High Contrast */
    .metric-card {
        background: #0D1526; padding: 25px; border-radius: 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #1C2C4E;
        text-align: center;
    }
    .hero-label { font-size: 10px; letter-spacing: 2px; color: #8E8E93; text-transform: uppercase; margin-bottom: 8px;}
    .hero-val { font-size: 28px; margin: 0; font-weight: 700; color: #FFFFFF; }
    
    /* Warning/Red Cards */
    .warning-card {
        background: #2D0A0A; border-left: 5px solid #FF5252;
        padding: 15px; border-radius: 10px; margin: 10px 0; color: #FFBABA;
    }
    
    /* Input Fields Fix */
    .stNumberInput input { background-color: #1C2C4E !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
DB_FILES = {
    "expenses": ["Date", "Category", "Amount", "Type"],
    "budgets": ["Category", "Amount", "Type", "DueDay"],
    "leftover": ["Date", "Source", "Amount", "Note"],
    "debt": ["Name", "Balance", "Payment", "DueDay"]
}

def load_vault(key):
    file = f"aura_{key}.csv"
    if os.path.exists(file):
        df = pd.read_csv(file)
        if 'Date' in df.columns: df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame(columns=DB_FILES[key])

for key in DB_FILES:
    if key not in st.session_state:
        st.session_state[key] = load_vault(key)

# --- 3. THE LEFTOVER & SUNDAY RESET LOGIC ---
def trigger_weekly_reset():
    """Moves unused weekly budget to Leftover Money (Simulated logic)"""
    # In a real app, we check if today is Sunday and if reset has happened.
    # For now, this is a manual trigger we can automate later.
    st.toast("Scanning for unused weekly funds...")

# --- 4. NAVIGATION ---
with st.sidebar:
    st.title("🏛️ AURA")
    page = st.radio("COMMAND", ["Dashboard", "Monthly Budget", "Weekly Budget", "Debt", "Insights", "Assistant"])
    st.markdown("---")
    st.markdown("### 💎 Executive Slide Panel")
    l_bal = st.session_state.leftover['Amount'].sum() if not st.session_state.leftover.empty else 0
    st.metric("LEFTOVER BALANCE", f"${l_bal:,.2f}")
    if st.button("Manual Sunday Reset"):
        trigger_weekly_reset()

# --- 5. PAGE: DASHBOARD ---
if page == "Dashboard":
    st.subheader("Financial Command Center")
    
    # Hero Calculations
    accounts = {"Checking": 8450.0, "Savings": 25000.0, "Retirement": 142000.0}
    total_debt = st.session_state.debt['Balance'].sum() if not st.session_state.debt.empty else 0
    net_worth = sum(accounts.values()) - total_debt
    
    # Top Row Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [("Net Worth", net_worth), ("Checking", accounts['Checking']), 
               ("Savings", accounts['Savings']), ("Retire", accounts['Retirement']), ("Debt", total_debt)]
    
    for i, (label, val) in enumerate(metrics):
        with [c1, c2, c3, c4, c5][i]:
            st.markdown(f'''<div class="metric-card"><div class="hero-label">{label}</div>
                        <div class="hero-val">${val:,.0f}</div></div>''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.markdown("#### Budget Utilization")
        if not st.session_state.expenses.empty:
            fig = px.pie(st.session_state.expenses, values='Amount', names='Category', hole=.7, 
                         color_discrete_sequence=px.colors.sequential.Golds)
            fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=0, r=0), height=350, 
                              paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Vault is currently empty. Log activity in Monthly/Weekly pages.")

    with col_side:
        st.markdown("#### Advisor Insights")
        if l_bal > 0:
            st.success(f"You have ${l_bal:,.2f} in Leftover Money to cover overspending.")
        else:
            st.warning("Leftover Money is zero. Overspending will hit Checking.")
        
        st.markdown("##### Upcoming Bills")
        st.caption("• Rent (Apr 1) - $2,400")
        st.caption("• Car Note (Apr 12) - $450")

# --- 6. PAGE: MONTHLY BUDGET ---
elif page == "Monthly Budget":
    st.subheader("Monthly Strategy")
    
    # Fixed Category: Savings
    st.info("Note: Monthly Savings goal is fixed at $1,000 as per strategy.")
    
    with st.expander("➕ Add Monthly Budget Category"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        amt = c2.number_input("Budget Amount", min_value=0.0)
        day = st.slider("Due Day", 1, 31, 15)
        if st.button("Secure Category"):
            new_row = pd.DataFrame([[name, amt, "Monthly", day]], columns=DB_FILES["budgets"])
            st.session_state.budgets = pd.concat([st.session_state.budgets, new_row], ignore_index=True)
            st.session_state.budgets.to_csv("aura_budgets.csv", index=False)
            st.rerun()

    # Budget List
    for i, row in st.session_state.budgets[st.session_state.budgets['Type'] == 'Monthly'].iterrows():
        with st.container():
            cols = st.columns([3, 2, 2, 1])
            cols[0].write(f"**{row['Category']}** (Day {row['DueDay']})")
            cols[1].write(f"Limit: ${row['Amount']:,.0f}")
            log_amt = cols[2].number_input("Add Spending", key=f"mo_{i}", min_value=0.0)
            if cols[3].button("Log", key=f"btn_mo_{i}"):
                new_ex = pd.DataFrame([[datetime.now(), row['Category'], log_amt, "Monthly"]], columns=DB_FILES["expenses"])
                st.session_state.expenses = pd.concat([st.session_state.expenses, new_ex], ignore_index=True)
                st.session_state.expenses.to_csv("aura_expenses.csv", index=False)
                st.rerun()

# --- 7. PAGE: DEBT ---
elif page == "Debt":
    st.subheader("Debt Command")
    with st.container():
        c1, c2 = st.columns(2)
        d_name = c1.text_input("Debt Name")
        d_bal = c2.number_input("Balance", min_value=0.0)
        d_pay = c1.number_input("Min Payment", min_value=0.0)
        d_day = c2.number_input("Payment Due Day", 1, 31, 1)
        if st.button("Add Debt"):
            new_d = pd.DataFrame([[d_name, d_bal, d_pay, d_day]], columns=DB_FILES["debt"])
            st.session_state.debt = pd.concat([st.session_state.debt, new_d], ignore_index=True)
            st.session_state.debt.to_csv("aura_debt.csv", index=False)
            st.rerun()
    
    if not st.session_state.debt.empty:
        st.markdown("#### Debt Portfolio")
        st.dataframe(st.session_state.debt, use_container_width=True)

# --- 8. PAGE: ASSISTANT ---
elif page == "Assistant":
    st.subheader("Aura Advisor")
    st.chat_message("assistant").write("Welcome to your private command center. I am monitoring your leftover transfers and debt due dates.")
    st.chat_input("Ask about your leftover balance...")
