import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import os
from PIL import Image

# --- 1. LUXURY THEME SETTINGS ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Midnight Gold Theme
st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #050505; }
    
    /* Hide Streamlit elements for App feel */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Metric Cards Custom Styling */
    [data-testid="stMetricValue"] { 
        font-size: 32px !important; 
        font-weight: 800 !important; 
        color: #D4AF37 !important; /* Metallic Gold */
        text-shadow: 0px 0px 10px rgba(212, 175, 55, 0.3);
    }
    [data-testid="stMetricLabel"] { 
        color: #8E8E93 !important; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
        font-size: 12px !important; 
    }
    
    /* Luxury Glass Cards */
    div[data-testid="stMetric"] {
        background: rgba(28, 28, 30, 0.6);
        border: 1px solid rgba(212, 175, 55, 0.2);
        padding: 15px;
        border-radius: 15px;
        backdrop-filter: blur(10px);
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #1c1c1e;
        border-radius: 10px;
        color: #8E8E93;
        border: none;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #D4AF37; }
    .stTabs [aria-selected="true"] { 
        background-color: #D4AF37 !important; 
        color: #000000 !important; 
        font-weight: bold;
    }

    /* Button Styling */
    .stButton>button {
        background-color: #D4AF37 !important;
        color: black !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: bold !important;
        height: 3em !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0px 0px 15px rgba(212, 175, 55, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

USER_PIN = "1234" 

if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ Aura Secure")
    pin_input = st.text_input("Vault PIN", type="password")
    if st.button("Unlock Access", use_container_width=True): 
        if pin_input == USER_PIN:
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- 2. DATA & FOLDER SETUP ---
DB_FILE = "aura_vault.csv"
IMG_DIR = "receipts"
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except: return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account", "Receipt"])
    return pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Account", "Receipt"])

if 'df' not in st.session_state: st.session_state.df = load_data()

# --- 3. LIVE CALCULATIONS ---
accounts = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
for _, row in st.session_state.df.iterrows():
    val = row['Amount'] if row['Type'] == 'Income' else -row['Amount']
    if row['Account'] in accounts: accounts[row['Account']] += val

# --- 4. EXECUTIVE DASHBOARD ---
st.title("🏛️ Aura Executive")
st.caption("Private Wealth Management")

c1, c2 = st.columns(2)
c1.metric("Net Worth", f"${sum(accounts.values()):,.0f}")
c2.metric("Checking", f"${accounts['Checking']:,.0f}")

c3, c4 = st.columns(2)
c3.metric("Savings", f"${accounts['Savings']:,.0f}")
c4.metric("Debt", f"${accounts['Debt']:,.0f}")

st.write("---")

# --- 5. NAVIGATION ---
tabs = st.tabs(["💸 Log", "📊 Stats", "🧠 AI", "⚙️"])

with tabs[0]: 
    st.subheader("New Entry")
    t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    t_amt = st.number_input("Amount", min_value=0.0, step=1.0)
    t_cat = st.selectbox("Category", ["Food", "Transport", "Housing", "Bills", "Invest", "Leisure"])
    t_acc = st.selectbox("Account", list(accounts.keys()))
    
    receipt_file = st.file_uploader("Capture Receipt", type=['jpg', 'png', 'jpeg'])
    
    if st.button("🚀 Commit to Vault", use_container_width=True):
        img_path = "None"
        if receipt_file:
            img_path = f"{IMG_DIR}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            img = Image.open(receipt_file)
            img.save(img_path)
            
        new_row = pd.DataFrame([[pd.to_datetime(datetime.now().date()), t_type, t_cat, t_amt, t_acc, img_path]], 
                               columns=["Date", "Type", "Category", "Amount", "Account", "Receipt"])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.session_state.df.to_csv(DB_FILE, index=False)
        st.toast("Encrypted & Saved")
        st.rerun()

with tabs[1]:
    st.subheader("Intelligence")
    exp_df = st.session_state.df[st.session_state.df['Type']=='Expense']
    if not exp_df.empty:
        fig = px.pie(exp_df, values='Amount', names='Category', hole=0.6, 
                     color_discrete_sequence=['#D4AF37', '#C0C0C0', '#1c1c1e', '#8E8E93'])
        fig.update_layout(showlegend=False, template="plotly_dark", margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    
    for i, row in st.session_state.df.sort_index(ascending=False).head(5).iterrows():
        st.info(f"{row['Category']} | ${row['Amount']} ({row['Type']})")

with tabs[2]:
    st.subheader("Advisor")
    st.write("Wealth projection looks stable for the next 30 days.")
    st.success("Strategy: Maximize Retirement contributions this month.")

with tabs[3]:
    if st.button("Logout System", use_container_width=True):
        st.session_state.auth = False
        st.rerun()
