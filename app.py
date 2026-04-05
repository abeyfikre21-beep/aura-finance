import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import os

# --- 1. CONFIG & PREMIUM STYLING ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #FFFFFF; }
    header { visibility: hidden; }
    
    /* Sidebar Drawer Styling */
    section[data-testid="stSidebar"] { 
        background-color: #121212 !important; 
        border-right: 1px solid rgba(212, 175, 55, 0.2); 
    }
    
    /* Executive Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(28, 28, 30, 0.9);
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 20px;
        padding: 20px;
    }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; font-size: 32px !important; font-weight: 800 !important; }
    
    /* Progress Bar Color */
    .stProgress > div > div > div > div { background-color: #D4AF37; }

    /* Hero Section */
    .hero {
        background: linear-gradient(180deg, #1c1c1e 0%, #050505 100%);
        padding: 40px;
        border-radius: 30px;
        text-align: center;
        border: 1px solid rgba(212, 175, 55, 0.15);
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
DB_FILE = "aura_vault.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except:
            return pd.DataFrame(columns=["Date", "Category", "Amount", "Period"])
    return pd.DataFrame(columns=["Date", "Category", "Amount", "Period"])

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- 3. THE SIDEBAR (ROCKET MONEY DRAWER) ---
with st.sidebar:
    st.title("🏛️ Aura Executive")
    st.markdown("---")
    
    st.subheader("👤 Profile")
    st.caption("Status: Platinum Member")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("⚙️ Preferences")
    view_mode = st.radio("Cycle", ["Weekly", "Monthly"])
    currency = st.selectbox("Currency", ["USD ($)", "EUR (€)", "GBP (£)"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🎯 Goals")
    target = st.number_input(f"Target {view_mode} Budget", value=1200 if view_mode == "Weekly" else 4500)
    
    st.markdown("---")
    if st.button("🗑️ Reset Vault"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.df = pd.DataFrame(columns=["Date", "Category", "Amount", "Period"])
        st.rerun()

# --- 4. CALCULATIONS ---
df = st.session_state.df
today = datetime.now()

if view_mode == "Weekly":
    start_date = today - timedelta(days=today.weekday())
    label = "This Week"
else:
    start_date = today.replace(day=1)
    label = "This Month"

current_data = df[df['Date'] >= pd.to_datetime(start_date)]
total_spent = current_data['Amount'].sum() if not current_data.empty else 0.0
remaining = target - total_spent
progress = min(total_spent / target, 1.0) if target > 0 else 0

# --- 5. MAIN DASHBOARD ---
st.markdown(f"""
    <div class="hero">
        <div style="color: #8E8E93; font-size: 14px; letter-spacing: 2px;">{label.upper()} SPENDING</div>
        <div style="color: #D4AF37; font-size: 60px; font-weight: 900; margin: 10px 0;">${total_spent:,.2f}</div>
        <div style="color: #8E8E93; font-size: 16px;">Remaining: ${max(remaining, 0):,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

st.progress(progress)

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total Expenses", f"{len(current_data)} Events")
with c2:
    top_cat = current_data.groupby('Category')['Amount'].sum().idxmax() if not current_data.empty else "N/A"
    st.metric("Top Category", top_cat)
with c3:
    status = "Under" if remaining > 0 else "Over"
    st.metric("Budget Status", status)

st.markdown("<br>", unsafe_allow_html=True)

tabs = st.tabs(["💸 Log", "📂 Vault", "📊 Insights", "🧠 Advisor"])

with tabs[0]: # LOGGING
    st.subheader("New Entry")
    col_a, col_b = st.columns(2)
    cat = col_a.selectbox("Category", ["Housing", "Insurance", "Car", "Groceries", "Gas", "Phone", "Gym", "Subscription", "Other"])
    amt = col_b.number_input("Amount Paid", min_value=0.0, step=0.01)
    date_entry = st.date_input("Transaction Date", datetime.now())
    
    if st.button("🚀 Secure Entry", use_container_width=True):
        if amt > 0:
            new_entry = pd.DataFrame([[pd.to_datetime(date_entry), cat, amt, view_mode]], 
                                     columns=["Date", "Category", "Amount", "Period"])
            st.session_state.df = pd.concat([st.session_state.df, new_entry], ignore_index=True)
            st.session_state.df.to_csv(DB_FILE, index=False)
            st.success(f"Added ${amt:.2f} to {cat}")
            st.rerun()

with tabs[1]: # VAULT (DELETE)
    st.subheader("Vault Management")
    if st.session_state.df.empty:
        st.info("Vault is empty.")
    else:
        for i, row in st.session_state.df.sort_values(by="Date", ascending=False).iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                c1.write(f"**{row['Date'].strftime('%Y-%m-%d')}**")
                c2.write(f"{row['Category']}")
                c3.write(f"${row['Amount']:,.2f}")
                if c4.button("🗑️", key=f"del_{i}"):
                    st.session_state.df = st.session_state.df.drop(i)
                    st.session_state.df.to_csv(DB_FILE, index=False)
                    st.rerun()
                st.markdown("---")

with tabs[2]: # INSIGHTS (CHARTS)
    st.subheader("Spending Analysis")
    if not current_data.empty:
        fig = px.pie(current_data, values='Amount', names='Category', hole=0.6,
                     template="plotly_dark", color_discrete_sequence=px.colors.sequential.Golds)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Daily Burn Rate")
        daily = current_data.groupby(current_data['Date'].dt.date)['Amount'].sum()
        st.plotly_chart(px.bar(daily, template="plotly_dark", color_discrete_sequence=['#D4AF37']), use_
