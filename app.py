import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import asyncio
from telegram import Bot
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# --- CONFIGURATION (TOKEN အသစ် ထည့်သွင်းပြီး) ---
TOKEN = "8797384581:AAHN2awLJgzsUPnJgOBr4WFBM2E-ysscUE4"
CHAT_ID = "8344079627"
TRADE_AED = 500 

# ၁ မိနစ်တစ်ခါ Auto-refresh လုပ်ခြင်း
st_autorefresh(interval=1 * 60 * 1000, key="quantum_forex_v4")

if "history" not in st.session_state:
    st.session_state.history = []

def calculate_rsi(series, window=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=window-1, adjust=False).mean()
    ema_down = down.ewm(com=window-1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

st.title("🌐 Quantum Forex Master V4")
st.markdown(f"**Chat ID:** `{CHAT_ID}` | **Trade Mode:** 500 AED")

# --- ASSET SELECTION ---
major_pairs = {
    "EUR/USD (Euro)": "EURUSD=X",
    "GBP/USD (Pound)": "GBPUSD=X",
    "USD/JPY (Yen)": "JPY=X",
    "Gold (XAU/USD)": "GC=F",
    "Bitcoin (BTC/USD)": "BTC-USD"
}

asset_label = st.selectbox("🎯 Select Asset", list(major_pairs.keys()))
ticker_symbol = major_pairs[asset_label]

try:
    # ဈေးကွက်ဒေတာ ဆွဲယူခြင်း
    data = yf.download(ticker_symbol, period="2d", interval="1m", progress=False)
    
    if not data.empty:
        data['RSI'] = calculate_rsi(data['Close'])
        current_price = float(data['Close'].iloc[-1])
        current_rsi = float(data['RSI'].iloc[-1])
        
        # --- TEST LOGIC (Noti မြန်မြန်တက်စေရန်) ---
        action = "WAIT"
        if current_rsi < 40: action = "BUY"
        elif current_rsi > 60: action = "SELL"

        # Live Display
        c1, c2, c3 = st.columns(3)
        price_format = "{:.5f}" if "USD" in asset_label else "{:.2f}"
        c1.metric("Live Price", price_format.format(current_price))
        c2.metric("RSI (14)", f"{current_rsi:.2f}")
        c3.metric("Action", action)

        # --- TELEGRAM SENDING ---
        if action != "WAIT":
            # Signal တစ်ခုကို တစ်ကြိမ်သာ ပို့ရန်
            h_key = f"v4_{ticker_symbol}_{action}"
            if h_key not in st.session_state:
                now = datetime.now().strftime("%H:%M:%S")
                
                async def send_now():
                    try:
                        bot = Bot(token=TOKEN)
                        msg = (f"🚀 **QUANTUM SIGNAL**\nAsset: {asset_label}\n"
                               f"Action: {action}\nPrice: {price_format.format(current_price)}\n"
                               f"Time: {now}\nTrade: {TRADE_AED} AED")
                        await bot.send_message(chat_id=CHAT_ID, text=msg)
                        st.success("✅ Telegram Noti ပို့ပြီးပါပြီ!")
                    except Exception as e:
                        st.error(f"❌ Telegram Error: {e}")

                asyncio.run(send_now())
                st.session_state.history.append({"Pair": asset_label, "Time": now, "Action": action})
                st.session_state[h_key] = True

        # Log Table
        if st.session_state.history:
            st.divider()
            st.subheader("📋 Trade Logs")
            st.table(pd.DataFrame(st.session_state.history).tail(5))

except Exception as e:
    st.error(f"System Error: {e}")
