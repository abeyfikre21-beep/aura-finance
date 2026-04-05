import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import os
from PIL import Image

# --- 1. MOBILE-FIRST SETTINGS ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 700; color: #00f2ff; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 15px; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

USER_PIN = "1234" 

if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔒 Aura Mobile")
    pin_input = st.text_input("Enter PIN", type="password")
    if st.button("Unlock", use_container_width=True): 
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

# --- 3. LOGIC ---
today = pd.to_datetime(datetime.now().date())
accounts = {"Checking": 5000, "Savings": 15000, "Retirement": 45000, "Debt": -2500}
for _, row in st.session_state.df.iterrows():
    val = row['Amount'] if row['Type'] == 'Income' else -row['Amount']
    if row['Account'] in accounts: accounts[row['Account']] += val

# --- 4. MOBILE DASHBOARD ---
st.title("🏛️ Aura Executive")
c1, c2 = st.columns(2)
c1.metric("Net Worth", f"${sum(accounts.values()):,.0f}")
c2.metric("Checking", f"${accounts['Checking']:,.0f}")

# --- 5. NAVIGATION ---
tabs = st.tabs(["💸 Log", "📊 Stats", "🧠 AI", "⚙️"])

with tabs[0]: # Log with Camera Support
    st.subheader("New Entry")
    t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    t_amt = st.number_input("Amount", min_value=0.0, step=1.0)
    t_cat = st.selectbox("Category", ["Food", "Transport", "Housing", "Bills", "Invest", "Leisure"])
    t_acc = st.selectbox("Account", list(accounts.keys()))
    
    # NEW: Camera/Upload Feature
    receipt_file = st.file_uploader("Capture Receipt", type=['jpg', 'png', 'jpeg'])
    
    if st.button("🚀 Save Transaction", use_container_width=True):
        img_path = "None"
        if receipt_file:
            img_path = f"{IMG_DIR}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            img = Image.open(receipt_file)
            img.save(img_path)
            
        new_row = pd.DataFrame([[today, t_type, t_cat, t_amt, t_acc, img_path]], 
                               columns=["Date", "Type", "Category", "Amount", "Account", "Receipt"])
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.session_state.df.to_csv(DB_FILE, index=False)
        st.toast("Saved with Receipt!")
        st.rerun()

with tabs[1]:
    st.subheader("History")
    # Show history with receipt view option
    for i, row in st.session_state.df.sort_index(ascending=False).head(10).iterrows():
        with st.expander(f"{row['Date'].strftime('%m/%d')} - {row['Category']}: ${row['Amount']}"):
            st.write(f"Type: {row['Type']} | Account: {row['Account']}")
            if row['Receipt'] != "None" and os.path.exists(row['Receipt']):
                st.image(row['Receipt'], caption="Stored Receipt")

with tabs[2]:
    st.subheader("AI Insights")
    st.info(f"Burn Rate: ${st.session_state.df[st.session_state.df['Type']=='Expense']['Amount'].tail(7).mean():,.2f}/day")
    st.success("Safe to invest $500 this week.")

with tabs[3]:
    if st.button("Logout", use_container_width=True):
        st.session_state.auth = False
        st.rerun()
