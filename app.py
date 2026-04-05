import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# --- 1. CONFIG & REFINED DARK THEME ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Playfair+Display:wght@700&display=swap');
    .stApp { background-color: #02060E; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #D4AF37; }
    
    @media (min-width: 1024px) {
        .main-container { max-width: 600px; margin: 0 auto; }
    }

    .budget-card {
        background: #0D1526; padding: 20px; border-radius: 15px;
        border: 1px solid #1C2C4E; margin-bottom: 12px;
    }
    .stat-label { font-size: 10px; color: #8E8E93; text-transform: uppercase; letter-spacing: 1px; }
    .stat-val { font-size: 18px; font-weight: 700; margin-top: 4px; }
    .status-tag { font-size: 10px; padding: 3px 10px; border-radius: 6px; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
DB_FILES = ["expenses", "budgets", "leftover", "debt"]

def load_vault(key):
    file = f"aura_{key}.csv"
    cols = {
        "expenses": ["Date", "Category", "Amount", "Type"],
        "budgets": ["Category", "Amount", "Type", "DueDay"],
        "leftover": ["Date", "Source", "Amount", "Note"],
        "debt": ["Name", "Balance", "Payment", "DueDay"]
    }
    if os.path.exists(file):
        df = pd.read_csv(file)
        if 'Date' in df.columns: df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame(columns=cols[key])

# Initialize session state for all dataframes
for key in DB_FILES:
    if key not in st.session_state:
        st.session_state[key] = load_vault(key)

def save_all():
    for key in DB_FILES:
        st.session_state[key].to_csv(f"aura_{key}.csv", index=False)

# --- 3. CORE PAGE RENDERER ---
def render_budget_page(type_label):
    st.title(f"🏛️ {type_label} Budget")
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    with st.expander(f"➕ Add {type_label} Category", expanded=False):
        name = st.text_input("Category Name")
        limit = st.number_input("Limit Amount ($)", min_value=0.0, step=50.0)
        if st.button("Create Category", use_container_width=True):
            if name:
                new_row = pd.DataFrame([[name, limit, type_label, 1]], columns=["Category", "Amount", "Type", "DueDay"])
                st.session_state.budgets = pd.concat([st.session_state.budgets, new_row], ignore_index=True)
                save_all()
                st.rerun()

    st.markdown("---")

    # Filter budgets by current page type
    items = st.session_state.budgets[st.session_state.budgets['Type'] == type_label]
    
    if items.empty:
        st.info(f"No {type_label} categories defined yet.")
    else:
        for i, row in items.iterrows():
            # Calculate total spent for this specific category
            category_expenses = st.session_state.expenses[st.session_state.expenses['Category'] == row['Category']]
            spent = category_expenses['Amount'].sum() if not category_expenses.empty else 0.0
            
            rem = row['Amount'] - spent
            status = "OVER LIMIT" if rem < 0 else "ON TRACK"
            status_color = "#FF5252" if rem < 0 else "#2ECC71"

            # The Card UI
            st.markdown(f"""
            <div class="budget-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <span style="font-size: 20px; font-weight: 800; color: #D4AF37;">{row['Category']}</span>
                    <span class="status-tag" style="background: {status_color}; color: white;">{status}</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                    <div><div class="stat-label">Limit</div><div class="stat-val">${row['Amount']:,.0f}</div></div>
                    <div><div class="stat-label">Spent</div><div class="stat-val">${spent:,.2f}</div></div>
                    <div><div class="stat-label">Left</div><div class="stat-val" style="color:{status_color}">${rem:,.2f}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action Row
            c1, c2, c3 = st.columns([3, 2, 1])
            add_val = c1.number_input("Amount", key=f"amt_{type_label}_{i}", min_value=0.0, label_visibility="collapsed")
            if c2.button("Log Spend", key=f"log_{type_label}_{i}", use_container_width=True):
                if add_val > 0:
                    new_ex = pd.DataFrame([[datetime.now(), row['Category'], add_val, type_label]], columns=["Date", "Category", "Amount", "Type"])
                    st.session_state.expenses = pd.concat([st.session_state.expenses, new_ex], ignore_index=True)
                    save_all()
                    st.rerun()
            
            if c3.button("🗑️", key=f"del_{type_label}_{i}"):
                # Delete category and wipe its specific history
                st.session_state.budgets = st.session_state.budgets.drop(i)
                st.session_state.expenses = st.session_state.expenses[st.session_state.expenses['Category'] != row['Category']]
                save_all()
                st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. NAVIGATION ---
with st.sidebar:
    st.title("🏛️ AURA")
    page = st.radio("MENU", ["Dashboard", "Monthly Budget", "Weekly Budget", "Debt", "Assistant"])
    st.markdown("---")
    l_bal = st.session_state.leftover['Amount'].sum() if not st.session_state.leftover.empty else 0
    st.metric("LEFTOVER POOL", f"${l_bal:,.2f}")

if page == "Weekly Budget":
    render_budget_page("Weekly")
elif page == "Monthly Budget":
    render_budget_page("Monthly")
elif page == "Dashboard":
    st.subheader("Financial Command Center")
    st.info("Log your budgets in the Weekly or Monthly sections to see insights here.")
elif page == "Debt":
    st.subheader("Debt Portfolio")
elif page == "Assistant":
    st.subheader("Aura AI Advisor")
