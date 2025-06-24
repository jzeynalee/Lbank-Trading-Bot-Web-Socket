import pandas as pd
import numpy as np
from scipy.signal import argrelextrema

class IndicatorCalculator:
    def __init__(self, df):
        self.df = df.copy()

    def calculate_rsi(self, period=14):
        delta = self.df['close_price'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        self.df['rsi'] = 100 - (100 / (1 + rs))
        return self

    def calculate_macd(self, fast=12, slow=26, signal=9):
        ema_fast = self.df['close_price'].ewm(span=fast).mean()
        ema_slow = self.df['close_price'].ewm(span=slow).mean()
        self.df['macd'] = ema_fast - ema_slow
        self.df['macd_signal'] = self.df['macd'].ewm(span=signal).mean()
        self.df['macd_hist'] = self.df['macd'] - self.df['macd_signal']
        return self

    def detect_candlestick_patterns(self):
        df = self.df
        df['bullish_candle'] = df['close_price'] > df['open_price']
        df['bearish_candle'] = df['close_price'] < df['open_price']
        df['body'] = abs(df['close_price'] - df['open_price'])
        df['range'] = df['high_price'] - df['low_price']
        df['upper_shadow'] = df['high_price'] - df[['close_price', 'open_price']].max(axis=1)
        df['lower_shadow'] = df[['close_price', 'open_price']].min(axis=1) - df['low_price']
        df['doji'] = df['body'] <= (df['range'] * 0.1)
        df['hammer'] = (df['lower_shadow'] > 2 * df['body']) & (df['upper_shadow'] < df['body']) & df['bullish_candle']
        df['inv_hammer'] = (df['upper_shadow'] > 2 * df['body']) & (df['lower_shadow'] < df['body']) & df['bullish_candle']
        df['bullish_engulfing'] = (
            df['bullish_candle'] &
            (df['open_price'] < df['close_price'].shift(1)) &
            (df['close_price'] > df['open_price'].shift(1)) &
            df['bearish_candle'].shift(1)
        )
        df['bearish_engulfing'] = (
            df['bearish_candle'] &
            (df['open_price'] > df['close_price'].shift(1)) &
            (df['close_price'] < df['open_price'].shift(1)) &
            df['bullish_candle'].shift(1)
        )
        df['bullish_score'] = df[['hammer', 'inv_hammer', 'bullish_engulfing']].sum(axis=1)
        df['bearish_score'] = df[['bearish_engulfing']].sum(axis=1)

        def classify(row):
            if row['doji']:
                return "Neutral"
            if row['bullish_score'] > row['bearish_score']:
                return "Bullish"
            elif row['bearish_score'] > row['bullish_score']:
                return "Bearish"
            else:
                return "Neutral"

        df['patterns_result'] = df.apply(classify, axis=1)
        return self

    def get_df(self):
        return self.df
