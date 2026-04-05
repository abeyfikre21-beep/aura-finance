import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. SETTINGS & EXECUTIVE DARK THEME ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #02060E; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #D4AF37; }
    
    /* Hero Section Styling */
    .hero-card {
        background: #0D1526; padding: 25px 10px; border-radius: 15px;
        border: 1px solid #1C2C4E; text-align: center;
    }
    .hero-label { font-size: 11px; color: #8E8E93; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; font-weight: 600;}
    .hero-val { font-size: 26px; font-weight: 800; color: #FFFFFF; }
    
    /* Budget Card Styling */
    .budget-card {
        background: #0D1526; padding: 18px; border-radius: 12px;
        border: 1px solid #1C2C4E; margin-bottom: 10px;
    }
    .stat-label { font-size: 10px; color: #8E8E93; text-transform: uppercase; }
    .stat-val { font-size: 18px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
DB_FILES = ["expenses", "budgets", "debt"]
def load_vault(key):
    file = f"aura_{key}.csv"
    if os.path.exists(file):
        df = pd.read_csv(file)
        if 'Date' in df.columns: df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame()

for key in DB_FILES:
    if key not in st.session_state:
        st.session_state[key] = load_vault(key)

# --- 3. SIDEBAR (GLOBAL CONTROLS) ---
with st.sidebar:
    st.title("🏛️ AURA")
    page = st.radio("MENU", ["Dashboard", "Monthly Budget", "Weekly Budget", "Debt"])
    st.markdown("---")
    st.subheader("🏦 Asset Management")
    # You can update these live to see your Net Worth change
    val_checking = st.number_input("Checking", value=8450, step=100)
    val_savings = st.number_input("Savings", value=25000, step=500)
    val_retire = st.number_input("Retirement", value=142000, step=1000)
    
    total_debt = st.session_state.debt['Balance'].sum() if not st.session_state.debt.empty else 0
    net_worth = (val_checking + val_savings + val_retire) - total_debt

# --- 4. DASHBOARD RENDERER ---
def draw_hero(col, label, value, color="#FFFFFF"):
    html = f"""
    <div class="hero-card">
        <div class="hero-label">{label}</div>
        <div class="hero-val" style="color:{color}">${value:,.0f}</div>
    </div>
    """
    col.markdown(html, unsafe_allow_html=True)

if page == "Dashboard":
    st.title("Executive Dashboard")
    
    # TOP HERO SECTION (THE 5 PILLARS)
    h1, h2, h3, h4, h5 = st.columns(5)
    draw_hero(h1, "Net Worth", net_worth, color="#D4AF37") # Gold highlight
    draw_hero(h2, "Checking Account", val_checking)
    draw_hero(h3, "Savings", val_savings)
    draw_hero(h4, "Retirement Fund", val_retire)
    draw_hero(h5, "Total Debt", total_debt, color="#FF5252") # Red highlight

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🏛️ Pinned Budget Essentials")
    
    # Specific Categories Pinned to Front Page
    pinned = [
        {"name": "Rent/Mortgage", "lim": 2400}, 
        {"name": "Groceries", "lim": 600}, 
        {"name": "Savings Goal", "lim": 1000}
    ]
    
    p_cols = st.columns(3)
    for idx, item in enumerate(pinned):
        exp_df = st.session_state.expenses
        spent = exp_df[exp_df['Category'] == item['name']]['Amount'].sum() if not exp_df.empty else 0
        with p_cols[idx]:
            card_html = f"""
            <div class="budget-card">
                <div class="stat-label">{item["name"]}</div>
                <div class="stat-val">${spent:,.0f} <small style="color:#8E8E93;">/ ${item["lim"]:,.0f}</small></div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            # Subtle progress bar
            progress = min(spent/item['lim'], 1.0) if item['lim'] > 0 else 0
            st.progress(progress)

# --- 5. OTHER PAGES (LOGIC) ---
elif page == "Debt":
    st.title("Debt Portfolio")
    # (Existing debt management logic here)

elif page in ["Weekly Budget", "Monthly Budget"]:
    st.title(f"{page} Management")
    # (Existing budget management logic here)
