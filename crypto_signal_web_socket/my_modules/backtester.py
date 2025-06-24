import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from my_modules.indicator import IndicatorCalculator
from my_modules.strategy import IchimokuDayStrategy
from my_modules.utils import log_signal
from my_modules.slippage_model import apply_slippage_and_commission
from my_modules.dashboard_generator import generate_dashboard
import time
import requests

# تبدیل تایم‌فریم WebSocket به REST API
TIMEFRAME_MAP_REST = {
    "1min": "minute1",
    "5min": "minute5",
    "15min": "minute15",
    "1h": "hour1",
    "4h": "hour4"
}

# لیست جفت‌ارزهای تست
ALL_PAIRS = ['btc_usdt', 'eth_usdt']
ALL_INTERVALS = ["1min", "5min", "15min", "1h", "4h"]

# تبدیل رشته تایم‌فریم به دقیقه
def interval_to_minutes(interval):
    if interval.endswith("min"):
        return int(interval.replace("min", ""))
    elif interval.endswith("h"):
        return int(interval.replace("h", "")) * 60
    else:
        raise ValueError(f"Unsupported interval format: {interval}")

# گرفتن دیتا از REST API
def fetch_historical_kline(pair, interval, size=200):
    rest_interval = TIMEFRAME_MAP_REST.get(interval)
    if not rest_interval:
        raise ValueError(f"Unsupported interval: {interval}")
    minutes_per_candle = interval_to_minutes(interval)
    start_time = int(time.time()) - size * 60 * minutes_per_candle
    url = "https://api.lbkex.com/v2/kline.do"
    params = {
        "symbol": pair,
        "size": size,
        "type": rest_interval,
        "time": str(start_time)
    }
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if "data" not in data:
            return None
        df = pd.DataFrame(data["data"], columns=[
            "timestamp", "open_price", "high_price", "low_price", "close_price", "volume"
        ])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
        df.set_index("timestamp", inplace=True)
        return df
    except Exception as e:
        print(f"[Error] Fetching {pair} @ {interval}: {e}")
        return None

# تحلیل یک جفت‌ارز در یک تایم‌فریم
def analyze_one(pair, interval, trade_log):
    df = fetch_historical_kline(pair, interval)
    if df is None or len(df) < 30:
        return

    df = IndicatorCalculator(df)\
        .calculate_rsi()\
        .calculate_macd()\
        .calculate_bollinger()\
        .calculate_keltner()\
        .calculate_ichimoku()\
        .detect_candlestick_patterns()\
        .detect_price_action()\
        .get_df()

    strat = StrategyEngine({"TTF": df})
    signal = strat.analyze_signal()\
                  .analyze_entry()\
                  .generate_signal()

    if signal in ["Buy", "Sell"]:
        entry = df.iloc[-2]
        exit_ = df.iloc[-1]
        slip = apply_slippage_and_commission(entry["close_price"], exit_["close_price"])
        trade_log.append({
            "symbol": pair,
            "interval": interval,
            "timestamp": exit_.name.isoformat(),
            "price": exit_["close_price"],
            "signal": signal,
            "return": slip["net_return"]
        })
        log_signal(f"[Backtest] {signal} {pair.upper()} @ {exit_['close_price']:.2f} | Return: {slip['net_return']:.4f}")

# اجرای کامل بک‌تست
def run_full_backtest():
    print("[🚀] Running backtest...")
    trade_log = []
    for pair in ALL_PAIRS:
        for interval in ALL_INTERVALS:
            analyze_one(pair, interval, trade_log)

    if trade_log:
        df_log = pd.DataFrame(trade_log)
        df_log.to_csv("backtest_log.csv", index=False)
        generate_dashboard(trade_log, output_html="backtest_report.html")
    else:
        print("⚠️ No trades were generated.")

if __name__ == "__main__":
    run_full_backtest()
