import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import asyncio
from telegram import Bot
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = "8797384581:AAF0lqlYmLUbexXDyEpEwta1RJ3IsuKAJYI"
CHAT_ID = "8344079627"
TRADE_AED = 500 

# ၂ မိနစ်တစ်ခါ Auto-refresh လုပ်ခြင်း
st_autorefresh(interval=2 * 60 * 1000, key="quantum_forex_loop")

if "history" not in st.session_state:
    st.session_state.history = []

# --- QUANTUM ANALYTICS FUNCTIONS ---
def quantum_probability_check(rsi, price_series):
    """Quantum-inspired momentum analysis"""
    momentum = price_series.diff().iloc[-1]
    q_score = (rsi / 100)
    if momentum > 0: q_score += 0.07
    else: q_score -= 0.07
    return np.clip(q_score, 0, 1)

def calculate_rsi(series, window=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=window-1, adjust=False).mean()
    ema_down = down.ewm(com=window-1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

st.title("🌌 Quantum Integrated Forex Bot")
st.markdown(f"**Trade Mode:** 500 AED Fixed Position")

# --- ASSET SELECTION ---
major_pairs = {
    "EUR/USD (Euro)": "EURUSD=X",
    "GBP/USD (Pound)": "GBPUSD=X",
    "USD/JPY (Yen)": "JPY=X",
    "AUD/USD (Aussie)": "AUDUSD=X",
    "Gold (XAU/USD)": "GC=F",
    "Bitcoin (BTC/USD)": "BTC-USD"
}

asset_label = st.selectbox("🎯 Select Asset", list(major_pairs.keys()))
ticker_symbol = major_pairs[asset_label]

try:
    data = yf.download(ticker_symbol, period="5d", interval="1m", progress=False)
    
    if not data.empty and len(data) > 30:
        data['RSI'] = calculate_rsi(data['Close'])
        current_price = float(data['Close'].iloc[-1])
        current_rsi = float(data['RSI'].iloc[-1])
        
        # Quantum Score Calculation
        q_prob = quantum_probability_check(current_rsi, data['Close'])
        
        # Strategy Logic
        action = "WAIT"
        if current_rsi < 32 and q_prob < 0.45: action = "STRONG BUY"
        elif current_rsi > 68 and q_prob > 0.55: action = "STRONG SELL"

        forecast = "Bullish" if q_prob < 0.5 else "Bearish"

        # --- LIVE DASHBOARD ---
        st.subheader(f"📊 {asset_label} Live Status")
        col1, col2, col3 = st.columns(3)
        
        price_format = "{:.5f}" if "USD" in asset_label else "{:.2f}"
        col1.metric("Live Price", price_format.format(current_price))
        col2.metric("Quantum Score", f"{q_prob:.2%}")
        col3.metric("RSI", f"{current_rsi:.2f}")

        st.info(f"🔮 **AI Forecast:** {forecast} | **Action:** {action}")
        
        # --- TELEGRAM NOTIFICATION ---
        if action != "WAIT":
            h_key = f"quantum_{ticker_symbol}"
            if h_key not in st.session_state or st.session_state[h_key] != action:
                now = datetime.now().strftime("%H:%M:%S")
                st.session_state.history.append({
                    "Pair": asset_label, "Time": now, "Action": action, 
                    "Price": price_format.format(current_price)
                })
                
                async def send_alert():
                    bot = Bot(token=TOKEN)
                    msg = (f"🌌 **QUANTUM FOREX ALERT**\n\n"
                           f"Asset: {asset_label}\n"
                           f"Action: {action}\n"
                           f"Price: {price_format.format(current_price)}\n"
                           f"Trade: {TRADE_AED} AED\n"
                           f"Quantum Score: {q_prob:.2%}")
                    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

                asyncio.run(send_alert())
                st.session_state[h_key] = action

        # --- HISTORY ---
        st.divider()
        st.subheader("📋 Daily Win/Loss Analysis")
        if st.session_state.history:
            st.table(pd.DataFrame(st.session_state.history).tail(10))
        else:
            st.write("ယနေ့အတွက် Signal မှတ်တမ်း မရှိသေးပါ။")

except Exception as e:
    st.warning("ဈေးကွက်ဒေတာများကို Quantum Algorithm ဖြင့် ချိတ်ဆက်နေဆဲဖြစ်ပါသည်။")
