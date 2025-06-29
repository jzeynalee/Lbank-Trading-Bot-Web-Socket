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
from utils.logger import get_logger

# === CONFIG ===
API_KEY = "your_api_key"
API_SECRET = "your_secret_key"
EQUITY = 10000
SIGNAL_FILE = "signals.csv"

# === LOGGER ===
logger = get_logger("app")

# === COMPONENTS ===
planner = TradePlanner(equity=EQUITY)
trader = Trader(api_key=API_KEY, secret_key=API_SECRET)
notifier = Notifier()
checker = SignalChecker(signal_file=SIGNAL_FILE, trader=trader, notifier=notifier)

# === INIT SIGNAL DB ===
if not os.path.exists(SIGNAL_FILE):
    pd.DataFrame(columns=["symbol", "entry", "direction", "sl", "tp", "position_size", "status"]).to_csv(SIGNAL_FILE, index=False)
    logger.info("Created new signal file: signals.csv")

# === SIGNAL HANDLER ===
def on_new_signal(signal: dict, atr: float):
    trade_plan = planner.plan_trade(signal, atr)
    logger.info(f"[TRADE PLAN] {trade_plan}")

    response = trader.place_order(
        symbol=trade_plan["symbol"],
        side=trade_plan["direction"],
        amount=trade_plan["position_size"],
        price=trade_plan["entry"],
        order_type="market"
    )
    logger.info(f"[ORDER SENT] {response}")

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
    logger.info(f"Logged new trade for {signal['symbol']} at {signal['entry']}")

# === TICK HANDLER ===
def on_tick():
    checker.check_signals()

# === WEBSOCKET MAIN ===
async def handle_ws():
    url = "wss://www.lbkex.net/ws/V2/"
    try:
        async with websockets.connect(url) as ws:
            for symbol in ["btc_usdt", "eth_usdt"]:
                sub_msg = json.dumps({
                    "action": "subscribe",
                    "subscribe": f"ticker.{symbol}"
                })
                await ws.send(sub_msg)
                logger.info(f"Subscribed to {symbol} ticker")

            logger.info("[WS] WebSocket connection established")

            while True:
                try:
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
                                logger.info(f"[SIGNAL DETECTED] {signal}")
                                on_new_signal(signal, atr)

                        on_tick()

                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"[ERROR IN WS LOOP] {str(e)}")
                    await asyncio.sleep(5)

    except Exception as e:
        logger.critical(f"[FATAL] Could not connect to WebSocket: {str(e)}")

# === ENTRY POINT ===
if __name__ == "__main__":
    logger.info("[APP START] Starting real-time trading bot...")
    asyncio.run(handle_ws())
