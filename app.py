import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf
from datetime import datetime
import os
from PIL import Image

# --- 1. FIXED LUXURY THEME ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');

    /* Clean up the top bar and background */
    .stApp { background-color: #F9F7F5; color: #1A1A1A; }
    header {visibility: hidden;} /* Removes the "double_arrow_right" glitch */
    
    /* Typography */
    h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #0A192F !important; }
    p, span, label { font-family: 'Inter', sans-serif !important; }

    /* The "Hero Card" - High Contrast */
    .hero-card {
        background: #0A192F;
        color: #FFFFFF !important;
        padding: 40px;
        border-radius: 24px;
        box-shadow: 0 15px 30px rgba(10, 25, 47, 0.15);
        margin-bottom: 25px;
        text-align: center;
    }
    .hero-label { font-size: 13px; opacity: 0.8; text-transform: uppercase; letter-spacing: 1.5px; color: #FFFFFF; }
    .hero-number { font-size: clamp(40px, 8vw, 60px); font-family: 'Playfair Display', serif; margin: 10px 0; color: #FFFFFF; }

    /* Secondary Metric Cards - Fixed Visibility */
    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #E5E1DA !important;
        border-radius: 16px !important;
        padding: 20px !important;
    }
    /* Force metric text to be dark/visible */
    [data-testid="stMetricValue"] { color: #0A192F !important; font-size: 32px !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #666666 !important; font-size: 14px !important; }
    
    /* Clean Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #888888 !important;
        font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] { color: #0A192F !important; border-bottom: 2px solid #0A192F !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTH & DATA ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<div style='text-align:center; padding-top:100px;'><h1>🏛️ Aura</h1></div>", unsafe_allow_html=True)
    if st.text_input("Vault PIN", type="password", key="login_pin") == "1234":
        st.session_state.auth = True
        st.rerun()
    st.stop()

DB_FILE = "aura_vault.csv"
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account", "Receipt"])

st.session_state.df = load_data()
