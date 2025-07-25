# -------------------------------
# ✅ INSTALL DEPENDENCIES FIRST:
# Replit Shell → pip install yfinance pandas_ta flask
# -------------------------------

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
import requests
import threading
from flask import Flask

# -------------------------------
# 🔐 TELEGRAM BOT CONFIG
# -------------------------------
bot_token = "8156823863:AAGp63jn7s3gMyQGwTGnDQh235OqpJVRAhU"
chat_id = "6510634018"

# -------------------------------
# 📤 SEND ALERT TO TELEGRAM
# -------------------------------
def send_alert(msg):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

# -------------------------------
# 📊 ENGULFING CANDLE LOGIC
# -------------------------------
def is_bullish_engulfing(curr, prev):
    return (
        prev["Close"] < prev["Open"] and
        curr["Close"] > curr["Open"] and
        curr["Close"] > prev["Open"] and
        curr["Open"] < prev["Close"]
    )

def is_bearish_engulfing(curr, prev):
    return (
        prev["Close"] > prev["Open"] and
        curr["Close"] < curr["Open"] and
        curr["Close"] < prev["Open"] and
        curr["Open"] > prev["Close"]
    )

# -------------------------------
# 🤖 SCALPING BOT FUNCTION
# -------------------------------
def run_bot():
    send_alert("✅ Bot started and connected to Telegram!")

    print("✅ Bot running 24/7...")

    while True:
        try:
            # 📥 Download 5m data from Yahoo Finance
            df_5m = yf.download("GC=F", interval="5m", period="1d")
            df_5m.ta.ema(length=9, append=True)
            df_5m.ta.ema(length=21, append=True)
            df_5m.ta.rsi(length=14, append=True)
            df_5m.ta.atr(length=14, append=True)

            # 📥 Download 15m data for trend direction
            df_15m = yf.download("GC=F", interval="15m", period="1d")
            df_15m.ta.ema(length=50, append=True)
            trend_15m = "Bullish" if df_15m["EMA_50"].iloc[-1] < df_15m["Close"].iloc[-1] else "Bearish"

            # 🧪 Prepare data for signal detection
            last = df_5m.iloc[-1]
            prev = df_5m.iloc[-2]

            atr = round(last["ATR_14"], 2)
            rsi = round(last["RSI_14"], 2)

            if atr < 1.0:
                print("📉 ATR too low, skipping signal.")
                time.sleep(300)
                continue

            message = None

            # 🟢 BUY Signal
            if (
                last["EMA_9"] > last["EMA_21"] and
                rsi > 50 and
                is_bullish_engulfing(last, prev) and
                last["Close"] > prev["High"]
            ):
                entry = round(last["Close"], 2)
                sl = round(last["Low"] - 1.5, 2)
                tp = round(entry + (entry - sl) * 1.5, 2)
                message = (
                    f"🟢 BUY Signal on GC=F (Gold Futures, 5m)\n"
                    f"📈 Entry: {entry}\n🛑 SL: {sl} | 🎯 TP: {tp}\n"
                    f"✅ Bullish Engulfing Confirmed\n"
                    f"📊 RSI: {rsi} | ATR: {atr}\n"
                    f"⚠️ 15m Trend: {trend_15m}"
                )

            # 🔴 SELL Signal
            elif (
                last["EMA_9"] < last["EMA_21"] and
                rsi < 50 and
                is_bearish_engulfing(last, prev) and
                last["Close"] < prev["Low"]
            ):
                entry = round(last["Close"], 2)
                sl = round(last["High"] + 1.5, 2)
                tp = round(entry - (sl - entry) * 1.5, 2)
                message = (
                    f"🔴 SELL Signal on GC=F (Gold Futures, 5m)\n"
                    f"📉 Entry: {entry}\n🛑 SL: {sl} | 🎯 TP: {tp}\n"
                    f"✅ Bearish Engulfing Confirmed\n"
                    f"📊 RSI: {rsi} | ATR: {atr}\n"
                    f"⚠️ 15m Trend: {trend_15m}"
                )

            if message:
                send_alert(message)
                print("✅ Signal sent to Telegram!")
            else:
                print("🔍 No valid signal found.")

        except Exception as e:
            print(f"❌ Error: {e}")

        time.sleep(300)  # Wait 5 minutes before the next check

# -------------------------------
# 🌐 FLASK KEEP-ALIVE SERVER
# -------------------------------
app = Flask('')

@app.route('/')
def home():
    return "✅ Scalping Bot is Running (Ping OK)"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# -------------------------------
# 🧵 RUN WEB + BOT THREADS
# -------------------------------
threading.Thread(target=run_web).start()
threading.Thread(target=run_bot).start()