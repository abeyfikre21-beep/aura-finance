import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# --- 1. SET PAGE CONFIG (MUST BE FIRST) ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")

# --- 2. THE "QUIET LUXURY" CSS FIX ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');

    /* Background & Main Text */
    .stApp { background-color: #F9F7F5 !important; color: #1A1A1A !important; }
    
    /* Hide the technical header glitches */
    header { visibility: hidden !important; }
    
    /* Typography */
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #0A192F !important; }
    p, span, label { font-family: 'Inter', sans-serif !important; color: #1A1A1A !important; }

    /* The "Hero Card" */
    .hero-card {
        background: #0A192F;
        color: white !important;
        padding: 40px;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 25px;
    }
    .hero-label { font-size: 13px; opacity: 0.8; text-transform: uppercase; letter-spacing: 1.5px; color: white !important; }
    .hero-number { font-size: 50px; font-family: 'Playfair Display', serif; margin: 10px 0; color: white !important; }

    /* Cards & Metrics Visibility Fix */
    div[data-testid="stMetric"] {
        background: white !important;
        border: 1px solid #E5E1DA !important;
        border-radius: 16px !important;
        padding: 20px !important;
    }
    [data-testid="stMetricValue"] { color: #0A192F !important; font-size: 32px !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #666 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE LOGIC ---
if 'auth' not in st.session_state: st.session_state.auth = False

def main_app():
    # Load Data
    DB_FILE = "aura_vault.csv"
    df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame(columns=["Date", "Type", "Amount", "Account"])
    
    # Financial Totals
    accs = {"Checking": 5200, "Savings": 18400, "Retirement": 52000}
    total_nw = sum(accs.values())
    
    # 🏛️ TOP AREA: HERO CARD
    st.markdown(f"""
        <div class="hero-card">
            <div class="hero-label">Total Net Worth</div>
            <div class="hero-number">${total_nw:,.0f}</div>
            <div class="hero-label">Strategic Wealth Overview</div>
        </div>
        """, unsafe_allow_html=True)

    # 📊 DASHBOARD METRICS
    c1, c2, c3 = st.columns(3)
    c1.metric("Cash Reserves", f"${accs['Checking'] + accs['Savings']:,.0f}")
    c2.metric("Portfolio Value", f"${accs['Retirement']:,.0f}")
    c3.metric("Monthly Flow", "$3,420", delta="-12%")

    st.markdown("---")

    # 🧭 NAVIGATION
    tabs = st.tabs(["Overview", "Transactions", "Advisor"])
    
    with tabs[0]:
        st.subheader("Performance Trend")
        chart_data = pd.DataFrame(np.random.randn(10, 1).cumsum() + 100, columns=['Value'])
        st.plotly_chart(px.line(chart_data, template="plotly_white", color_discrete_sequence=['#0A192F']).update_layout(height=250), use_container_width=True)

    with tabs[2]:
        st.subheader("Private Wealth Advisor")
        st.text_input("Consult with Aura...", placeholder="Analyze my spending for March")

# --- 4. AUTH GATE ---
if not st.session_state.auth:
    st.title("🏛️ Aura Private Access")
    pin = st.text_input("Security PIN", type="password")
    if st.button("Unlock"):
        if pin == "1234":
            st.session_state.auth = True
            st.rerun()
else:
    main_app()
