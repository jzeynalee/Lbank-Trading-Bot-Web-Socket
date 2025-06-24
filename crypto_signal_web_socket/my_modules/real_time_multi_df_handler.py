from collections import defaultdict, deque
import pandas as pd
from my_modules.utils import fetch_initial_kline
from my_modules.indicator import IndicatorCalculator

class MultiTimeframeHandler:
    def __init__(self, symbol, timeframes, rest_code_map):
        self.symbol = symbol
        self.timeframes = timeframes
        self.rest_code_map = rest_code_map
        self.dataframes = defaultdict(lambda: pd.DataFrame())
        self.prefill_symbol_data()

    def prefill_symbol_data(self):
        print(f"⏳ Prefilling {self.symbol}...")
        for tf in self.timeframes:
            df = fetch_initial_kline(self.symbol, tf, size=200, rest_code_map=self.rest_code_map)
            if not df.empty:
                df = IndicatorCalculator(df) \
                        .calculate_rsi() \
                        .calculate_macd() \
                        .calculate_bollinger() \
                        .calculate_keltner() \
                        .calculate_ichimoku() \
                        .detect_candlestick_patterns() \
                        .detect_price_action() \
                        .get_df()
                self.dataframes[tf] = df
                print(f"✅ Initialized {self.symbol}-{tf} with {len(df)} rows")
            else:
                print(f"⚠️ Empty data for {self.symbol}-{tf}")

    def update_candle(self, timeframe, new_candle):
        df = self.dataframes.get(timeframe, pd.DataFrame())
        new_row = pd.DataFrame([{
            "timestamp": new_candle["timestamp"],
            "open": new_candle["open"],
            "high": new_candle["high"],
            "low": new_candle["low"],
            "close": new_candle["close"],
            "volume": new_candle["volume"]
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df = df.tail(200).copy()

        df = IndicatorCalculator(df) \
                .calculate_rsi() \
                .calculate_macd() \
                .calculate_bollinger() \
                .calculate_keltner() \
                .calculate_ichimoku() \
                .detect_candlestick_patterns() \
                .detect_price_action() \
                .get_df()

        self.dataframes[timeframe] = df

    def get_multi_df(self):
        return {
            "HHT": self.dataframes.get("4hr"),
            "HTF": self.dataframes.get("1hr"),
            "TTF": self.dataframes.get("15min"),
            "LTF": self.dataframes.get("5min"),
            "LLT": self.dataframes.get("1min")
        }

    def get_df(self, timeframe):
        return self.dataframes.get(timeframe)
