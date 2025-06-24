import os
from my_modules.real_time_multi_df_handler import MultiTimeframeHandler
from my_modules.strategy import strategyEngine
from my_modules.notifier.SignalDispatcher import SignalDispatcher
from my_modules.utils import load_config

# === CONFIG ===
CONFIG = load_config("config.json")

SYMBOLS = CONFIG["SYMBOLS"]
TIMEFRAMES = CONFIG["TIMEFRAMES"]
REST_TIMEFRAME_CODES = CONFIG["REST_TIMEFRAME_CODES"]
WEBSOCKET_TIMEFRAME_CODES = CONFIG["WEBSOCKET_TIMEFRAME_CODES"]

# === HANDLERS ===
handlers = {
    symbol: MultiTimeframeHandler(symbol, TIMEFRAMES, REST_TIMEFRAME_CODES)
    for symbol in SYMBOLS
}

# === SIGNAL NOTIFIER ===
notifier = SignalDispatcher(
    telegram_token=CONFIG["TELEGRAM"]["token"],
    telegram_chat_id=CONFIG["TELEGRAM"]["chat_id"],
    twitter_credentials=CONFIG["TWITTER"],
    linkedin_credentials=CONFIG["LINKEDIN"]
)

# This file will serve as the central entry point for config and passing to modules