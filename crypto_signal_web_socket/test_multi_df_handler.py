import pandas as pd
from my_modules.real_time_multi_df_handler import MultiTimeframeHandler
from my_modules.utils import load_config

def test_multi_df_handler():
    config = load_config("config.json")
    symbol = config["SYMBOLS"][0]  # مثلاً "btc_usdt"
    timeframes = config["TIMEFRAMES"]
    rest_map = config["REST_TIMEFRAME_CODES"]

    print(f"📊 Testing symbol: {symbol} with timeframes: {timeframes}")
    
    # ساخت handler و پر کردن داده‌های اولیه
    handler = MultiTimeframeHandler(symbol, timeframes, rest_map)

    # گرفتن دیتا از تمام تایم‌فریم‌ها با نام‌های معنایی (HHT, HTF, ...)
    multi_df = handler.get_multi_df()

    print("✅ get_multi_df() returned:\n")
    for role, df in multi_df.items():
        print(f"--- {role} ---")
        print(df.tail(2))  # نمایش آخرین ۲ کندل
        print("📌 Columns:", df.columns.tolist())
        print(f"Rows: {len(df)} | Columns: {len(df.columns)}\n")

if __name__ == "__main__":
    test_multi_df_handler()
