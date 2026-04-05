import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# --- 1. CONFIG & REFINED DARK THEME ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #02060E; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #D4AF37; }
    
    /* Center Column Constraint for Desktop */
    @media (min-width: 1024px) {
        .main-container { max-width: 600px; margin: 0 auto; }
    }

    /* High-Density Budget Card */
    .budget-card {
        background: #0D1526; padding: 15px; border-radius: 12px;
        border: 1px solid #1C2C4E; margin-bottom: 8px;
    }
    .stat-label { font-size: 10px; color: #8E8E93; text-transform: uppercase; }
    .stat-val { font-size: 16px; font-weight: 700; }
    .status-tag { font-size: 10px; padding: 2px 8px; border-radius: 4px; font-weight: 800; }
    
    /* Input Compactness */
    .stNumberInput div div input { padding: 5px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. REBUILT DATA ENGINE ---
DB_FILES = ["expenses", "budgets", "leftover", "debt"]

def load_vault(key):
    file = f"aura_{key}.csv"
    if os.path.exists(file):
        df = pd.read_csv(file)
        if 'Date' in df.columns: df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame() # Return empty to handle dynamic column creation

for key in DB_FILES:
    if key not in st.session_state:
        st.session_state[key] = load_vault(key)

def save_all():
    for key in DB_FILES:
        st.session_state[key].to_csv(f"aura_{key}.csv", index=False)

# --- 3. PAGE LOGIC: WEEKLY ---
def render_budget_page(type_label):
    st.markdown(f"### {type_label} Command")
    
    # WRAP IN CENTER CONTAINER
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # QUICK ADD
    with st.expander(f"➕ New {type_label}", expanded=False):
        name = st.text_input("Name")
        limit = st.number_input("Limit ($)", min_value=0.0)
        if st.button("Add"):
            new_row = pd.DataFrame([[name, limit, type_label, 1]], columns=["Category", "Amount", "Type", "DueDay"])
            st.session_state.budgets = pd.concat([st.session_state.budgets, new_row], ignore_index=True)
            save_all()
            st.rerun()

    st.markdown("---")

    # THE ALL-IN-ONE LIST
    items = st.session_state.budgets[st.session_state.budgets['Type'] == type_label]
    
    if items.empty:
        st.info("No categories active.")
    else:
        for i, row in items.iterrows():
            # Calculate Spent
            if not st.session_state.expenses.empty:
                spent = st.session_state.expenses[st.session_state.expenses['Category'] == row['Category']]['Amount'].sum()
            else:
                spent = 0
            
            rem = row['Amount'] - spent
            status = "OVER" if rem < 0 else "OK"
            status_color = "#FF5252" if rem < 0 else "#2ECC71"

            with st.container():
                st.markdown(f"""
                <div class="budget-card">
