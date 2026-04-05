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
    .stApp { background-color: #050A18; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #02060E !important; border-right: 1px solid #D4AF37; }
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #D4AF37 !important; }
    
    /* Metric Cards */
    .metric-card {
        background: #0D1526; padding: 20px; border-radius: 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #1C2C4E;
        text-align: center; margin-bottom: 10px;
    }
    .hero-label { font-size: 9px; letter-spacing: 2px; color: #8E8E93; text-transform: uppercase; margin-bottom: 5px;}
    .hero-val { font-size: 24px; font-weight: 700; color: #FFFFFF; }
    
    /* Budget Row Styling */
    .budget-row {
        background: #0D1526; padding: 15px; border-radius: 12px;
        border: 1px solid #1C2C4E; margin-bottom: 10px;
    }
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

# --- 3. NAVIGATION ---
with st.sidebar:
    st.title("🏛️ AURA")
    page = st.radio("COMMAND", ["Dashboard", "Monthly Budget", "Weekly Budget", "Debt", "Insights", "Assistant"])
    st.markdown("---")
    l_total = st.session_state.leftover['Amount'].sum() if not st.session_state.leftover.empty else 0
    st.metric("LEFTOVER BALANCE", f"${l_total:,.2f}")

# --- 4. PAGE: MONTHLY BUDGET ---
if page == "Monthly Budget":
    st.subheader("Monthly Command")
    
    # ADD SECTION
    with st.expander("➕ Add New Monthly Category", expanded=True):
        c1, c2, c3 = st.columns([3, 2, 1])
        new_name = c1.text_input("Category Name (e.g. Rent)")
        new_amt = c2.number_input("Monthly Limit ($)", min_value=0.0)
        new_day = c3.number_input("Due Day", 1, 31, 1)
        if st.button("Initialize Category", use_container_width=True):
            if new_name:
                new_row = pd.DataFrame([[new_name, new_amt, "Monthly", new_day]], columns=DB_FILES["budgets"])
                st.session_state.budgets = pd.concat([st.session_state.budgets, new_row], ignore_index=True)
                st.session_state.budgets.to_csv("aura_budgets.csv", index=False)
                st.rerun()

    st.markdown("---")
    
    # LIST & DELETE SECTION
    mo_items = st.session_state.budgets[st.session_state.budgets['Type'] == 'Monthly']
    if mo_items.empty:
        st.info("No monthly categories yet. Add one above.")
    else:
        for i, row in mo_items.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                col1.write(f"**{row['Category']}** (Day {row['DueDay']})")
                col2.write(f"Limit: ${row['Amount']:,.2f}")
                
                # Log Spend
                log_amt = col3.number_input("Log Spent", key=f"mo_log_{i}", min_value=0.0)
                if col4.button("Add", key=f"mo_btn_{i}"):
                    new_ex = pd.DataFrame([[datetime.now(), row['Category'], log_amt, "Monthly"]], columns=DB_FILES["expenses"])
                    st.session_state.expenses = pd.concat([st.session_state.expenses, new_ex], ignore_index=True)
                    st.session_state.expenses.to_csv("aura_expenses.csv", index=False)
                    st.rerun()
                
                # DELETE
                if col5.button("🗑️", key=f"mo_del_{i}"):
                    st.session_state.budgets = st.session_state.budgets.drop(i)
                    st.session_state.budgets.to_csv("aura_budgets.csv", index=False)
                    st.rerun()
            st.markdown("---")

# --- 5. PAGE: WEEKLY BUDGET ---
elif page == "Weekly Budget":
    st.subheader("Weekly Operations")
    
    # ADD SECTION
    with st.expander("➕ Add New Weekly Category", expanded=True):
        wc1, wc2 = st.columns([3, 2])
        w_name = wc1.text_input("Category Name (e.g. Groceries)")
        w_limit = wc2.number_input("Weekly Limit ($)", min_value=0.0)
        if st.button("Set Weekly Goal", use_container_width=True):
            if w_name:
                new_w = pd.DataFrame([[w_name, w_limit, "Weekly", 0]], columns=DB_FILES["budgets"])
                st.session_state.budgets = pd.concat([st.session_state.budgets, new_w], ignore_index=True)
                st.session_state.budgets.to_csv("aura_budgets.csv", index=False)
                st.rerun()

    st.markdown("---")

    # LIST & DELETE SECTION
    wk_items = st.session_state.budgets[st.session_state.budgets['Type'] == 'Weekly']
    if wk_items.empty:
        st.info("No weekly categories yet.")
    else:
        for i, row in wk_items.iterrows():
            spent = st.session_state.expenses[st.session_state.expenses['Category'] == row['Category']]['Amount'].sum()
            rem = row['Amount'] - spent
            
            with st.container():
                c_1, c_2, c_3, c_4, c_5 = st.columns([3, 2, 2, 2, 1])
                c_1.write(f"**{row['Category']}**")
                color = "#FF5252" if rem < 0 else "#D4AF37"
                c_2.markdown(f"<span style='color:{color}'>Rem: ${rem:,.2f}</span>", unsafe_allow_html=True)
                
                # Log Spend
                w_log = c_3.number_input("Log", key=f"wk_log_{i}", min_value=0.0)
                if c_4.button("Add", key=f"wk_btn_{i}"):
                    new_ex = pd.DataFrame([[datetime.now(), row['Category'], w_log, "Weekly"]], columns=DB_FILES["expenses"])
                    st.session_state.expenses = pd.concat([st.session_state.expenses, new_ex], ignore_index=True)
                    st.session_state.expenses.to_csv("aura_expenses.csv", index=False)
                    st.rerun()
                
                # DELETE
                if c_5.button("🗑️", key=f"wk_del_{i}"):
                    st.session_state.budgets = st.session_state.budgets.drop(i)
                    st.session_state.budgets.to_csv("aura_budgets.csv", index=False)
                    st.rerun()
            st.markdown("---")

# --- DASHBOARD & DEBT PAGES (REMAIN THE SAME) ---
elif page == "Dashboard":
    st.subheader("Financial Command Center")
    # ... Dashboard Code from V5.0 ...
    st.write("Dashboard is active. Go to Weekly/Monthly to add categories.")

elif page == "Debt":
    st.subheader("Debt Portfolio")
    # ... Debt Code from V5.0 ...
    st.write("Debt management is active.")
