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

for key in DB_FILES:
    if key not in st.session_state:
        st.session_state[key] = load_vault(key)

def save_all():
    for key in DB_
