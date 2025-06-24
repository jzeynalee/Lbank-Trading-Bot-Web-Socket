class IchimokuDayStrategy:
    def __init__(self, multi_df):
        """
        multi_df = {
            'HHT': df_4h,
            'HTF': df_1h,
            'TTF': df_15min,
            'LTF': df_5min,
            'LLT': df_1min
        }
        """
        self.multi_df = multi_df

    def get_df(self, tf):
        return self.multi_df.get(tf)

    # --- مشترک‌ها ---
    def is_bullish_kumo(self, tf):
        df = self.get_df(tf)
        if df is None: return False
        return df['senkou_span_a'].iloc[-1] > df['senkou_span_b'].iloc[-1]

    def is_bearish_kumo(self, tf):
        df = self.get_df(tf)
        if df is None: return False
        return df['senkou_span_a'].iloc[-1] < df['senkou_span_b'].iloc[-1]

    def chikou_above_price(self, tf):
        df = self.get_df(tf)
        if df is None: return False
        return df['chikou_span'].iloc[-1] > df['close_price'].iloc[-1]

    def chikou_below_price(self, tf):
        df = self.get_df(tf)
        if df is None: return False
        return df['chikou_span'].iloc[-1] < df['close_price'].iloc[-1]

    def is_tenkan_kijun_cross_up(self, tf):
        df = self.get_df(tf)
        if df is None or len(df) < 2: return False
        return df['tenkan_sen'].iloc[-1] > df['kijun_sen'].iloc[-1] and \
               df['tenkan_sen'].iloc[-2] <= df['kijun_sen'].iloc[-2]

    def is_tenkan_kijun_cross_down(self, tf):
        df = self.get_df(tf)
        if df is None or len(df) < 2: return False
        return df['tenkan_sen'].iloc[-1] < df['kijun_sen'].iloc[-1] and \
               df['tenkan_sen'].iloc[-2] >= df['kijun_sen'].iloc[-2]

    def is_bullish_candle(self, tf):
        df = self.get_df(tf)
        if df is None: return False
        return df['patterns_result'].iloc[-1] == "Bullish"

    def is_bearish_candle(self, tf):
        df = self.get_df(tf)
        if df is None: return False
        return df['patterns_result'].iloc[-1] == "Bearish"

    def rsi_below(self, tf, threshold=40):
        df = self.get_df(tf)
        if df is None: return False
        return df['rsi'].iloc[-1] < threshold

    def rsi_above(self, tf, threshold=60):
        df = self.get_df(tf)
        if df is None: return False
        return df['rsi'].iloc[-1] > threshold

    def close_above_kijun(self, tf):
        df = self.get_df(tf)
        if df is None: return False
        return df['close_price'].iloc[-1] > df['kijun_sen'].iloc[-1]

    def close_below_kijun(self, tf):
        df = self.get_df(tf)
        if df is None: return False
        return df['close_price'].iloc[-1] < df['kijun_sen'].iloc[-1]

    # --- Buy Strategy ---
    def generate_signal(self):
        if not self.is_bullish_kumo('HHT'):
            return "NoTrend"

        if not (self.is_bullish_kumo('HTF') and self.chikou_above_price('HTF')):
            return "WeakTrend"

        if not (self.is_tenkan_kijun_cross_up('TTF') and self.is_bullish_candle('TTF') and self.rsi_below('TTF')):
            return "WeakSignal"

        if not self.close_above_kijun('LTF'):
            return "WaitLTF"

        if not self.is_bullish_candle('LLT'):
            return "WaitLLT"

        return "Buy"

    # --- Sell Strategy ---
    def generate_signal_sell(self):
        if not self.is_bearish_kumo('HHT'):
            return "NoTrend"

        if not (self.is_bearish_kumo('HTF') and self.chikou_below_price('HTF')):
            return "WeakTrend"

        if not (self.is_tenkan_kijun_cross_down('TTF') and self.is_bearish_candle('TTF') and self.rsi_above('TTF')):
            return "WeakSignal"

        if not self.close_below_kijun('LTF'):
            return "WaitLTF"

        if not self.is_bearish_candle('LLT'):
            return "WaitLLT"

        return "Sell"
