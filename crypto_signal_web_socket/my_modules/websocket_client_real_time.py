import requests
import asyncio
import websockets
import json
import time
from datetime import datetime
from my_modules.real_time_multi_df_handler import MultiTimeframeHandler
from my_modules.utils import load_config
from my_modules.strategy import strategyEngine
from my_modules.notifier.SignalDispatcher import SignalDispatcher

CONFIG = load_config('config.json')
SYMBOLS = CONFIG['SYMBOLS']
TIMEFRAMES = CONFIG['TIMEFRAMES']

WS_TIMEFRAME_CODES = CONFIG['WEBSOCKET_TIMEFRAME_CODES']

order_books = {symbol: {"bids": [], "asks": []} for symbol in SYMBOLS}

def fetch_order_book(symbol):
    try:
        url = f"https://api.lbank.info/v2/depth.do?symbol={symbol}&size=200"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data.get("asks") or not data.get("bids"):
            raise ValueError("Invalid order book response")
        return {"bids": data["bids"], "asks": data["asks"]}
    except Exception as e:
        print(f"[ERROR] Failed to fetch order book for {symbol}: {e}")
        return {"bids": [], "asks": []}

handlers = {
    symbol: MultiTimeframeHandler(symbol, TIMEFRAMES)
    for symbol in SYMBOLS
}

notifier = SignalDispatcher(
    telegram_token="YOUR_TELEGRAM_BOT_TOKEN",
    telegram_chat_id="YOUR_TELEGRAM_CHAT_ID",
    twitter_credentials={
        "api_key": "YOUR_API_KEY",
        "api_secret": "YOUR_API_SECRET",
        "access_token": "YOUR_ACCESS_TOKEN",
        "access_secret": "YOUR_ACCESS_SECRET"
    },
    linkedin_credentials={
        "username": "your_email@example.com",
        "password": "your_password"
    }
)

async def handle_socket(symbol, timeframe):
    uri = "wss://www.lbank.info/ws/V2"
    tf_code = WS_TIMEFRAME_CODES[timeframe]

    async with websockets.connect(uri) as ws:
        sub_msg = {
            "action": "subscribe",
            "subscribe": "kbar",
            "kbar": tf_code,
            "pair": symbol
        }
        await ws.send(json.dumps(sub_msg))
        print(f"[Subscribed] {symbol} @ {tf_code}")
        if timeframe == "1min":
            order_books[symbol] = fetch_order_book(symbol)
        

        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=60)
                data = json.loads(msg)

                if "ping" in data:
                    await ws.send(json.dumps({"action": "pong", "pong": data["ping"]}))
                    continue

                if data.get("data"):
                    tick = data["data"]
                    candle = {
                        "timestamp": int(tick["TS"]),
                        "open": float(tick["OPEN"]),
                        "high": float(tick["HIGH"]),
                        "low": float(tick["LOW"]),
                        "close": float(tick["CLOSE"]),
                        "volume": float(tick["V"])
                    }
                    handlers[symbol].update_candle(timeframe, candle)

                    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    multi_df = handlers[symbol].get_multi_df()

                    for tf_key, df in multi_df.items():
                        strategy = strategyEngine({tf_key: df})
                        signal = strategy.generate_signal(tf_key)

                        if signal in ["Buy", "Sell"]:
                            print(f"✅ [{timestamp}] {signal.upper()} Signal from {symbol} ({tf_key})")
                            notifier.send_all(symbol, signal, multi_df, tf_key, timestamp)
                        else:
                            print(f"⏳ [{timestamp}] {symbol} ({tf_key}): {signal}")

            except asyncio.TimeoutError:
                print(f"[Timeout] {symbol}-{timeframe} no response")
                break
            except Exception as e:
                print(f"[Error] {symbol}-{timeframe} => {e}")
                break

async def main():
    tasks = []
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            tasks.append(handle_socket(symbol, tf))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
