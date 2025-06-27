import asyncio
import websockets
import json
import pandas as pd
import os
import time
from datetime import datetime

from core import get_multi_df
from strategy import strategy_macd_ichimoku
from indicator import IndicatorCalculator
from trade_planner import TradePlanner
from trader import Trader
from signal_checker import SignalChecker
from notifier import Notifier

# === CONFIG ===
API_KEY = "your_api_key"
API_SECRET = "your_secret_key"
EQUITY = 10000
SIGNAL_FILE = "signals.csv"

# === COMPONENTS ===
planner = TradePlanner(equity=EQUITY)
trader = Trader(api_key=API_KEY, secret_key=API_SECRET)
notifier = Notifier()
checker = SignalChecker(signal_file=SIGNAL_FILE, trader=trader, notifier=notifier)

if not os.path.exists(SIGNAL_FILE):
    pd.DataFrame(columns=["symbol", "entry", "direction", "sl", "tp", "position_size", "status"]).to_csv(SIGNAL_FILE, index=False)

# === SIGNAL HANDLER ===
def on_new_signal(signal: dict, atr: float):
    trade_plan = planner.plan_trade(signal, atr)
    print(f"\n[TRADE PLAN] {trade_plan}")

    response = trader.place_order(
        symbol=trade_plan["symbol"],
        side=trade_plan["direction"],
        amount=trade_plan["position_size"],
        price=trade_plan["entry"],
        order_type="market"
    )
    print("[ORDER SENT]", response)

    df_log = pd.read_csv(SIGNAL_FILE)
    new_entry = {
        "symbol": trade_plan["symbol"],
        "entry": trade_plan["entry"],
        "direction": trade_plan["direction"],
        "sl": trade_plan["sl"],
        "tp": trade_plan["tp"],
        "position_size": trade_plan["position_size"],
        "status": "OPEN"
    }
    df_log = pd.concat([df_log, pd.DataFrame([new_entry])], ignore_index=True)
    df_log.to_csv(SIGNAL_FILE, index=False)

# === TICK HANDLER ===
def on_tick():
    checker.check_signals()

# === WEBSOCKET MAIN ===
async def handle_ws():
    url = "wss://www.lbkex.net/ws/V2/"
    async with websockets.connect(url) as ws:
        # Subscribe to ticker channel
        for symbol in ["btc_usdt", "eth_usdt"]:
            sub_msg = json.dumps({
                "action": "subscribe",
                "subscribe": f"ticker.{symbol}"
            })
            await ws.send(sub_msg)

        print("[WS] Subscribed to tickers")

        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            if 'ticker' in data.get('subscribe', ''):
                symbol = data['subscribe'].split('.')[-1]
                df = get_multi_df(symbol=symbol, limit=100)

                if df is not None:
                    calc = IndicatorCalculator(df)
                    df = calc.calculate_macd().calculate_ichimoku().get_df()

                    result = strategy_macd_ichimoku(df)
                    if result:
                        close = float(df['close_price'].iloc[-1])
                        atr = df['high_price'].rolling(14).max().iloc[-1] - df['low_price'].rolling(14).min().iloc[-1]

                        signal = {
                            "symbol": symbol,
                            "entry": close,
                            "direction": result  # "long" or "short"
                        }
                        on_new_signal(signal, atr)

                # Tick-level signal checking
                on_tick()

            await asyncio.sleep(1)

# === RUN ===
if __name__ == "__main__":
    asyncio.run(handle_ws())
