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
    
    section[data-testid="stSidebar"] { 
        background-color: #121212 !important; 
        border-right: 1px solid rgba(212, 175, 55, 0.2); 
    }
    
    div[data-testid="stMetric"] {
        background: rgba(28, 28, 30, 0.9);
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 20px;
        padding: 20px;
    }
    [data-testid="stMetricValue"] { color: #D4AF37 !important; font-size: 32px !important; font-weight: 800 !important; }
    
    .stProgress > div > div > div > div { background-color: #D4AF37; }

    .hero {
        background: linear-gradient(180deg, #1c1c1e 0%, #050505 100%);
        padding: 40px;
        border-radius: 30px;
        text-align: center;
        border: 1px solid rgba(212, 175, 55, 0.15);
        margin-bottom: 25px;
    }
    
    .stButton>button {
        background-color: #D4AF37 !important;
        color: black !important;
        border-radius: 10px !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
DB_FILE = "aura_vault.csv"

def load_data():
    if os.path.exists(DB_FILE):
