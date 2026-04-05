import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
import os

# --- 1. GLOBAL SETTINGS & LUXURY THEME ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

# Stone, Navy, and Bronze Palette
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    
    .stApp { background-color: #F4F1EE; color: #1A1A1A; }
    [data-testid="stSidebar"] { background-color: #0A192F !important; border-right: 1px solid #D4AF37; }
    
    /* Typography */
    h1, h2, h3, .hero-val { font-family: 'Playfair Display', serif !important; color: #0A192F; }
    p, span, label { font-family: 'Inter', sans-serif !important; }

    /* Dashboard Cards */
    .metric-card {
        background: white; padding: 25px; border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #E5E1DA;
        text-align: center;
    }
    .hero-label { font-size: 12px; letter-spacing: 2px; color: #8E8E93; text-transform: uppercase; }
    .hero-val { font-size: 38px; margin: 10px 0; }
    
    /* Warning Cards */
    .warning-card {
        background: #FFF5F5; border-left: 5px solid #FF5252;
        padding: 15px; border-radius: 10px; margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
def init_data(name, cols):
    file = f"aura_{name}.csv"
    if os.path.exists(file):
        df = pd.read_csv(file)
        if 'Date' in df.columns: df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame(columns=cols)

# Initialize Ledgers
if 'expenses' not in st.session_state: st.session_state.expenses = init_data("expenses", ["Date", "Category", "Amount", "Type"]) # Type: Weekly/Monthly
if 'budgets' not in st.session_state: st.session_state.budgets = init_data("budgets", ["Category", "Amount", "Type", "DueDay"])
if 'leftover' not in st.session_state: st.session_state.leftover = init_data("leftover", ["Date", "Source", "Amount", "Note"])
if 'debt' not in st.session_state: st.session_state.debt = init_data("debt", ["Name", "Balance", "Payment", "DueDay"])

# Mock Accounts (In a real app, these would be user-inputted)
accounts = {"Checking": 8450.00, "Savings": 25000.00, "Retirement": 142000.00}

# --- 3. LOGIC: LEFTOVER ENGINE & WEEKLY RESET ---
def process_weekly_reset():
    # This would check if current time > last Sunday reset
    # Logic: Move unused weekly budget to Leftover Ledger
    pass

# --- 4. NAVIGATION SIDEBAR ---
with st.sidebar:
    selected = option_menu(
        "Aura Terminal", 
        ["Dashboard", "Monthly Budget", "Weekly Budget", "Debt", "Insights", "Assistant"],
        icons=['house', 'calendar-month', 'calendar-week', 'bank', 'graph-up', 'magic'],
        menu_icon="cast", default_index=0,
        styles={"container": {"padding": "5!important", "background-color": "#0A192F"},
                "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "--hover-color": "#1C2C4E"},
                "nav-link-selected": {"background-color": "#D4AF37", "color": "black"}}
    )

# --- 5. PAGE: DASHBOARD ---
if selected == "Dashboard":
    st.markdown("### Executive Overview")
    
    # Calculation Logic
    total_debt = st.session_state.debt['Balance'].sum()
    net_worth = sum(accounts.values()) - total_debt
    total_spent_mo = st.session_state.expenses[st.session_state.expenses['Type'] == 'Monthly']['Amount'].sum()
    leftover_bal = st.session_state.leftover['Amount'].sum()

    # Top Hero Row
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        ("Net Worth", net_worth), ("Checking", accounts['Checking']),
        ("Savings", accounts['Savings']), ("Retirement", accounts['Retirement']),
        ("Total Debt", total_debt)
    ]
    for i, (label, val) in enumerate(metrics):
        with [c1, c2, c3, c4, c5][i]:
            st.markdown(f'<div class="metric-card"><div class="hero-label">{label}</div><div class="hero-val">${val:,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main Body
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("#### Capital Distribution")
        sub1, sub2, sub3 = st.columns(3)
        sub1.metric("Leftover Money", f"${leftover_bal:,.2f}")
        sub2.metric("Monthly Spent", f"${total_spent_mo:,.2f}")
        sub3.metric("Weekly Spent", "$0.00") # Placeholder for weekly logic
        
        # Spending Chart
        if not st.session_state.expenses.empty:
            fig = px.pie(st.session_state.expenses, values='Amount', names='Category', hole=.7, 
                         color_discrete_sequence=px.colors.sequential.Darkmint_r)
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Log your first expense in Monthly or Weekly pages to see the breakdown.")

    with col_right:
        st.markdown("#### Advisor Insights")
        if total_spent_mo > 4000:
            st.markdown('<div class="warning-card">⚠️ Monthly spending is 12% higher than average. Consider using leftover funds.</div>', unsafe_allow_html=True)
        
        st.markdown("##### Upcoming Bills")
        st.caption("Rent - Due in 3 days ($2,400)")
        st.caption("Car Note - Due in 12 days ($450)")

# --- 6. PAGE: MONTHLY BUDGET ---
elif selected == "Monthly Budget":
    st.markdown("### Monthly Command")
    
    with st.expander("➕ Add New Monthly Category"):
        c_name = st.text_input("Category Name")
        c_amt = st.number_input("Budget Amount", min_value=0.0)
        c_day = st.slider("Due Day", 1, 31, 1)
        if st.button("Initialize Category"):
            new_b = pd.DataFrame([[c_name, c_amt, "Monthly", c_day]], columns=st.session_state.budgets.columns)
            st.session_state.budgets = pd.concat([st.session_state.budgets, new_b], ignore_index=True)
            st.session_state.budgets.to_csv("aura_budgets.csv", index=False)
            st.rerun()

    # Display Categories
    if not st.session_state.budgets.empty:
        for i, row in st.session_state.budgets[st.session_state.budgets['Type'] == 'Monthly'].iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.write(f"**{row['Category']}** (Due: {row['DueDay']})")
            col2.write(f"Budget: ${row['Amount']:,.2f}")
            
            # Spent Input
            spent = col3.number_input("Log Spending", key=f"spent_{i}", min_value=0.0)
            if col4.button("Commit", key=f"btn_{i}"):
                new_ex = pd.DataFrame([[datetime.now(), row['Category'], spent, "Monthly"]], columns=st.session_state.expenses.columns)
                st.session_state.expenses = pd.concat([st.session_state.expenses, new_ex], ignore_index=True)
                st.session_state.expenses.to_csv("aura_expenses.csv", index=False)
                st.success("Log Updated")
                st.rerun()

# --- 7. PAGE: DEBT ---
elif selected == "Debt":
    st.markdown("### Liability Management")
    c1, c2 = st.columns(2)
    with c1:
        d_name = st.text_input("Debt Name")
        d_bal = st.number_input("Current Balance", min_value=0.0)
    with c2:
        d_pay = st.number_input("Monthly Payment", min_value=0.0)
        d_day = st.number_input("Due Day", 1, 31)
    
    if st.button("Add Debt Entry"):
        new_d = pd.DataFrame([[d_name, d_bal, d_pay, d_day]], columns=st.session_state.debt.columns)
        st.session_state.debt = pd.concat([st.session_state.debt, new_d], ignore_index=True)
        st.session_state.debt.to_csv("aura_debt.csv", index=False)
        st.rerun()

    st.table(st.session_state.debt)

# --- 8. ASSISTANT PAGE ---
elif selected == "Assistant":
    st.markdown("### Private Advisor")
    query = st.chat_input("Ask about your leftover balance or debt strategy...")
    if query:
        st.chat_message("assistant").write("Analyzing your Command Center data... Based on your current Checking balance and upcoming Car Note, I recommend keeping $1,200 in liquid cash this week.")
