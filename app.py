import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

st.set_page_config(
    page_title="Indian Stocks Alert",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .big-alert {
        font-size: 26px !important;
        font-weight: bold;
        padding: 18px;
        border-radius: 12px;
        text-align: center;
        margin: 10px 0;
    }
    .long { background-color: #0a7c42; color: white; }
    .short { background-color: #b91c1c; color: white; }
    .neutral { background-color: #1f2937; color: #d1d5db; }
</style>
""", unsafe_allow_html=True)

SWING_STOCKS = {
    "POWERINDIA.NS": "Hitachi Energy",
    "INDIGO.NS": "Indigo",
    "PGIL.NS": "Pearl Global",
    "MTARTECH.NS": "MTAR",
    "BOSCHLTD.NS": "Bosch",
    "ADANIENT.NS": "Adani Enterprise",
    "MRF.NS": "MRF",
    "RELIANCE.NS": "Reliance"
}

NIFTY_30M = {
    "RELIANCE.NS": "Reliance",
    "TCS.NS": "TCS",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "INFY.NS": "Infosys",
    "SBIN.NS": "SBI",
    "BHARTIARTL.NS": "Airtel",
    "ITC.NS": "ITC",
    "LT.NS": "L&T",
    "ADANIENT.NS": "Adani Ent"
}

def calculate_indicators(df):
    if df is None or len(df) < 25:
        return None
    df = df.copy()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['BB_MID'] = df['Close'].rolling(20).mean()
    df['BB_STD'] = df['Close'].rolling(20).std()
    df['BB_UPPER'] = df['BB_MID'] + 2 * df['BB_STD']
    df['BB_LOWER'] = df['BB_MID'] - 2 * df['BB_STD']
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['VOL_SMA'] = df['Volume'].rolling(20).mean()
    return df

def get_signal(df):
    if df is None or len(df) < 25:
        return "NO DATA", "neutral"
    last = df.iloc[-1]
    prev = df.iloc[-2]
    long_cond = (
        last['Close'] > last['EMA20'] and
        last['EMA20'] > prev['EMA20'] and
        last['RSI'] > 50 and
        last['Close'] > last['BB_MID'] and
        last['Volume'] > last['VOL_SMA']
    )
    short_cond = (
        last['Close'] < last['EMA20'] and
        last['EMA20'] < prev['EMA20'] and
        last['RSI'] < 50 and
        last['Close'] < last['BB_MID'] and
        last['Volume'] > last['VOL_SMA']
    )
    if long_cond:
        return "🟢 LONG SETUP", "long"
    elif short_cond:
        return "🔴 SHORT SETUP", "short"
    else:
        return "⚪ No Setup", "neutral"

def fetch_data(symbol, interval, period="60d"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return None
        return calculate_indicators(df)
    except:
        return None

def resample_to_4h(df_1h):
    if df_1h is None or df_1h.empty:
        return None
    df = df_1h.resample('4h').agg({
        'Open': 'first', 'High': 'max', 'Low': 'min',
        'Close': 'last', 'Volume': 'sum'
    }).dropna()
    return calculate_indicators(df)

st.title("📈 Indian Stocks Live Alert")
st.caption(f"Updated: {datetime.now().strftime('%d %b %Y %H:%M')} IST")

if st.button("🔄 Refresh Now", use_container_width=True):
    st.rerun()

st.header("🔥 Swing Stocks (4H + Daily)")

for symbol, name in SWING_STOCKS.items():
    st.subheader(f"{name}")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**4 Hour**")
        df_1h = fetch_data(symbol, "1h", "60d")
        df_4h = resample_to_4h(df_1h)
        signal, css = get_signal(df_4h)
        if df_4h is not None and len(df_4h) > 0:
            last = df_4h.iloc[-1]
            st.markdown(f'<div class="big-alert {css}">{signal}</div>', unsafe_allow_html=True)
            st.write(f"Price: ₹{last['Close']:.1f} | RSI: {last['RSI']:.0f}")
            st.caption(f"EMA20: ₹{last['EMA20']:.1f}")
        else:
            st.warning("No data")
    
    with col2:
        st.markdown("**Daily**")
        df_d = fetch_data(symbol, "1d", "1y")
        signal_d, css_d = get_signal(df_d)
        if df_d is not None and len(df_d) > 0:
            last = df_d.iloc[-1]
            st.markdown(f'<div class="big-alert {css_d}">{signal_d}</div>', unsafe_allow_html=True)
            st.write(f"Price: ₹{last['Close']:.1f} | RSI: {last['RSI']:.0f}")
            st.caption(f"EMA20: ₹{last['EMA20']:.1f}")
        else:
            st.warning("No data")
    st.divider()

st.header("⚡ Nifty Stocks – 30 Min")

cols = st.columns(2)
i = 0
for symbol, name in NIFTY_30M.items():
    with cols[i % 2]:
        df_30 = fetch_data(symbol, "30m", "60d")
        signal, css = get_signal(df_30)
        st.markdown(f"**{name}**")
        if df_30 is not None and len(df_30) > 0:
            last = df_30.iloc[-1]
            st.markdown(f'<div class="big-alert {css}">{signal}</div>', unsafe_allow_html=True)
            st.caption(f"₹{last['Close']:.1f} | RSI {last['RSI']:.0f}")
        else:
            st.warning("No data")
    i += 1

time.sleep(120)
st.rerun()
