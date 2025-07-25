# -------------------------------
# ✅ INSTALL DEPENDENCIES:
# pip install yfinance pandas pandas_ta flask requests
# -------------------------------

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
import threading
import requests
from flask import Flask

# -------------------------------
# 🔐 TELEGRAM CONFIG
# -------------------------------
bot_token = "8156823863:AAGp63jn7s3gMyQGwTGnDQh235OqpJVRAhU"
chat_id = "6510634018"

def send_alert(msg):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, data=data)

# -------------------------------
# 📊 ENGULFING CANDLE STRATEGY
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
# 🤖 MAIN BOT LOOP
# -------------------------------
def run_bot():
    print("✅ Bot started...")
    while True:
        try:
            df = yf.download("XAUUSD=X", interval="5m", period="1d")
            df.ta.ema(length=9, append=True)
            df.ta.ema(length=21, append=True)
            df.ta.macd(append=True)
            df.ta.rsi(length=14, append=True)
            df.ta.atr(length=14, append=True)
            df["Volume"] = df["Volume"].fillna(0)

            df15 = yf.download("XAUUSD=X", interval="15m", period="1d")
            df15.ta.ema(length=50, append=True)
            trend_15m = "Bullish" if df15["Close"].iloc[-1] > df15["EMA_50"].iloc[-1] else "Bearish"

            last = df.iloc[-1]
            prev = df.iloc[-2]

            atr = round(last["ATR_14"], 2)
            rsi = round(last["RSI_14"], 2)
            volume = int(last["Volume"])

            if atr < 1.0 or volume < 100:
                print("⚠️ ATR or Volume too low. Skipping.")
                time.sleep(300)
                continue

            message = None

            # BUY SIGNAL
            if (
                last["EMA_9"] > last["EMA_21"] and
                last["MACDh_12_26_9"] > 0 and
                rsi > 50 and
                is_bullish_engulfing(last, prev)
            ):
                entry = round(last["Close"], 2)
                sl = round(last["Low"] - 1.5, 2)
                tp = round(entry + (entry - sl) * 1.5, 2)
                message = (
                    f"🟢 BUY Signal on XAU/USD (5m)\n"
                    f"📈 Entry: {entry}\n🛑 SL: {sl} | 🎯 TP: {tp}\n"
                    f"📊 RSI: {rsi}, ATR: {atr}, Vol: {volume}\n"
                    f"📌 Trend: {trend_15m}"
                )

            # SELL SIGNAL
            elif (
                last["EMA_9"] < last["EMA_21"] and
                last["MACDh_12_26_9"] < 0 and
                rsi < 50 and
                is_bearish_engulfing(last, prev)
            ):
                entry = round(last["Close"], 2)
                sl = round(last["High"] + 1.5, 2)
                tp = round(entry - (sl - entry) * 1.5, 2)
                message = (
                    f"🔴 SELL Signal on XAU/USD (5m)\n"
                    f"📉 Entry: {entry}\n🛑 SL: {sl} | 🎯 TP: {tp}\n"
                    f"📊 RSI: {rsi}, ATR: {atr}, Vol: {volume}\n"
                    f"📌 Trend: {trend_15m}"
                )

            if message:
                send_alert(message)
                print("✅ Signal sent to Telegram.")
            else:
                print("🔍 No valid signal at this time.")

        except Exception as e:
            print(f"❌ Error: {e}")

        time.sleep(300)

# -------------------------------
# 🌐 FLASK KEEP-ALIVE SERVER
# -------------------------------
app = Flask('')

@app.route('/')
def home():
    return "✅ XAU Scalping Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_web).start()
threading.Thread(target=run_bot).start()