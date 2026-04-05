import streamlit as st
import pandas as pd
import os

# --- 1. THE "GHOST" CSS (Removes +/- and Boxes) ---
st.set_page_config(page_title="Aura Finance", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #02060E; color: #FFFFFF; }
    
    /* 1. HIDE THE + / - BUTTONS AND BORDERS */
    div[data-testid="stNumberInput"] label { display: none !important; }
    div[data-testid="stNumberInput"] { margin-top: -22px !important; }
    
    /* Force the input to look like static text */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; margin: 0; 
    }
    input[type=number] { -moz-appearance: textfield; }

    div[data-baseweb="input"] { 
        background-color: transparent !important; 
        border: none !important; 
        box-shadow: none !important;
    }

    input {
        background-color: transparent !important;
        color: white !important;
        font-weight: 800 !important;
        font-size: 28px !important;
        text-align: center !important;
        border: none !important;
        outline: none !important;
        width: 100% !important;
    }

    /* 2. THE CARDS */
    .hero-card {
        background: #0D1526; padding: 20px; border-radius: 15px; 
        border: 1px solid #D4AF37; text-align: center; height: 110px;
    }
    .detail-card {
        background: #090F1C; padding: 15px; border-radius: 10px; 
        border: 1px solid #1C2C4E; text-align: center; height: 95px;
    }
    .card-label { font-size: 11px; color: #8E8E93; text-transform: uppercase; font-weight: 700; margin-bottom: 5px;}
    .section-title { margin: 25px 0 15px 0; color: #8E8E93; font-size: 10px; text-transform: uppercase; letter-spacing: 4px; text-align: center;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
def quick_save(file, data):
    pd.DataFrame([data]).to_csv(file, index=False)

if 'acct' not in st.session_state:
    if os.path.exists("aura_accounts.csv"): st.session_state.acct = pd.read_csv("aura_accounts.csv").iloc[0].to_dict()
    else: st.session_state.acct = {"Checking": 0.0, "Savings": 0.0, "Retirement": 0.0}

if 'targs' not in st.session_state:
    keys = ["LeftToSpend", "Spent", "W_Budget", "W_Spent", "M_Budget", "M_Spent", "NextBill", "Upcoming", "Emergency", "Leftover", "Recs"]
    if os.path.exists("aura_targets.csv"): st.session_state.targs = pd.read_csv("aura_targets.csv").iloc[0].to_dict()
    else: st.session_state.targs = {k: 0.0 for k in keys}

# --- 3. DASHBOARD ---
st.markdown('<div class="section-title">Principal Status</div>', unsafe_allow_html=True)
h = st.columns(5)

# Net Worth (Static)
nw = sum(st.session_state.acct.values())
h[0].markdown(f'<div class="hero-card"><div class="card-label">Net Worth</div><div style="font-size:28px; font-weight:800; color:#D4AF37; margin-top:8px;">${nw:,.0f}</div></div>', unsafe_allow_html=True)

# EDITABLE HEROES (Checking, Savings, Retirement)
for i, name in enumerate(["Checking", "Savings", "Retirement"], 1):
    with h[i]:
        st.markdown(f'<div class="hero-card"><div class="card-label">{name}</div>', unsafe_allow_html=True)
        v = st.number_input(f"h_{name}", value=float(st.session_state.acct[name]), key=f"ac_{name}", step=1.0)
        if v != st.session_state.acct[name]:
            st.session_state.acct[name] = v
            quick_save("aura_accounts.csv", st.session_state.acct)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

h[4].markdown(f'<div class="hero-card"><div class="card-label">Total Debt</div><div style="font-size:28px; font-weight:800; color:#FF5252; margin-top:8px;">$0</div></div>', unsafe_allow_html=True)

# EDITABLE DETAILS
st.markdown('<div class="section-title">Budget Details</div>', unsafe_allow_html=True)

def draw_ghost(col, label, key):
    with col:
        st.markdown(f'<div class="detail-card"><div class="card-label">{label}</div>', unsafe_allow_html=True)
        v = st.number_input(f"d_{key}", value=float(st.session_state.targs.get(key, 0.0)), key=f"tg_{key}", step=1.0)
        if v != st.session_state.targs.get(key, 0.0):
            st.session_state.targs[key] = v
            quick_save("aura_targets.csv", st.session_state.targs)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

r1 = st.columns(4)
draw_ghost(r1[0], "Left To Spend", "LeftToSpend")
draw_ghost(r1[1], "Total Spent", "Spent")
draw_ghost(r1[2], "Weekly Budget", "W_Budget")
draw_ghost(r1[3], "Weekly Spent", "W_Spent")

r2 = st.columns(4)
draw_ghost(r2[0], "Monthly Budget", "M_Budget")
draw_ghost(r2[1], "Monthly Spent", "M_Spent")
draw_ghost(r2[2], "Next Bill", "NextBill")
draw_ghost(r2[3], "Upcoming Bills", "Upcoming")

r3 = st.columns(3)
draw_ghost(r3[0], "Emergency Fund", "Emergency")
draw_ghost(r3[1], "Leftover Money", "Leftover")
draw_ghost(r3[2], "Recommendations", "Recs")
