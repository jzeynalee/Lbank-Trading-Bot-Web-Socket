
import asyncio
import pandas as pd
from collections import defaultdict, deque
from my_modules.indicator import IndicatorCalculator
from my_modules.notifier.telegram import TelegramNotifier
from my_modules.notifier.twitter import TwitterNotifier
from my_modules.notifier.linkedin import LinkedInNotifier
from my_modules.db.signal_db import SignalDatabase
from my_modules.utils import log_signal, save_signal_to_excel, update_dashboard
from my_modules.strategy import StrategyEngine
from datetime import datetime
import threading

# استفاده از نسخه جدید WebSocket ترکیبی با prefill و پشتیبانی از REST-compatible timeframes
from websocket_client_combined_updated import LBankWebSocketClient

symbol_data = defaultdict(lambda: defaultdict(lambda: deque(maxlen=200)))

telegram = TelegramNotifier("YOUR_TELEGRAM_BOT_TOKEN", "YOUR_CHAT_ID")
twitter = TwitterNotifier("TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET")
db = SignalDatabase()

def heartbeat():
    import time
    while True:
        msg = f"✅ [{datetime.utcnow().isoformat()}] System is alive..."
        print(msg)
        log_signal(msg)
        time.sleep(10)

threading.Thread(target=heartbeat, daemon=True).start()

def on_kline(pair, interval, kline):
    df = pd.DataFrame([kline], columns=["timestamp", "open_price", "high_price", "low_price", "close_price", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
    symbol_data[pair][interval].append(df.iloc[0])

    if len(symbol_data[pair][interval]) >= 30:
        full_df = pd.DataFrame(symbol_data[pair][interval])
        full_df.set_index("timestamp", inplace=True)
        last = full_df.iloc[-1]

        timeframes = {'HHT': '4h', 'HTF': '1h', 'TTF': '15min', 'LTF': '5min', 'LLT': '1min'}
        multi_df = {}
        for tf_label, tf in timeframes.items():
            if len(symbol_data[pair][tf]) >= 30:
                df_tf = pd.DataFrame(symbol_data[pair][tf])
                df_tf.set_index("timestamp", inplace=True)
                df_tf = IndicatorCalculator(df_tf)                    .calculate_rsi()                    .calculate_ichimoku()                    .detect_candlestick_patterns()                    .get_df()
                multi_df[tf_label] = df_tf

        if len(multi_df) == 5:
            orderbook_mock = {'bids': [{'quantity': 500}], 'asks': [{'quantity': 400}]}
            strat = StrategyEngine(multi_df)
            signal = strat.analyze_trend()                          .analyze_signal()                          .analyze_entry()                          .analyze_scalping()                          .confirm_orderbook(orderbook_mock)                          .generate_signal()

            if signal in ['Buy', 'Sell']:
                msg = f"🚨 {signal.upper()} SIGNAL | {pair.upper()} [{interval}] @ {last['close_price']:.2f}"
                print(msg)
                telegram.send_message(msg)
                twitter.send_message(msg)
                db.save_signal(pair, interval, last.name.isoformat(), last['close_price'], signal)
                log_signal(msg)
                save_signal_to_excel("signals.xlsx", {
                    "symbol": pair, "interval": interval,
                    "timestamp": last.name.isoformat(),
                    "price": last["close_price"],
                    "signal": signal
                })
                update_dashboard("dashboard.html", db.get_signals())

async def run():
    client = LBankWebSocketClient(
        pairs=[
            'btc_usdt', 'eth_usdt', 'xrp_usdt', 'bnb_usdt', 'sol_usdt', 'doge_usdt',
            'ada_usdt', 'trx_usdt', 'link_usdt', 'sui_usdt', 'avax_usdt', 'arb_usdt',
            'matic_usdt', 'op_usdt', 'near_usdt', 'cro_usdt', 'gno_usdt', 'apt_usdt',
            'xmr_usdt', 'kava_usdt', 'ton_usdt', 'mnt_usdt', 'blast_usdt', 'algo_usdt',
            'rune_usdt', 'osmo_usdt', 'rsk_usdt', 'xin_usdt', 'celo_usdt', 'ftm_usdt',
            'eos_usdt', 'xtz_usdt', 'neo_usdt', 'ont_usdt', 'metis_usdt', 'leo_usdt'
        ],
        intervals=["1min", "5min", "15min", "1h", "4h"],
        on_kline_callback=on_kline,
        symbol_data=symbol_data
    )
    await client.connect()

if __name__ == "__main__":
    asyncio.run(run())
