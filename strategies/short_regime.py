import pandas as pd
from strategies.base import BaseStrategy


class ShortRegimeStrategy(BaseStrategy):
    """Bearish trend/pullback strategy used to time inverse ETF entries.

    SELL means bearish exposure is allowed (buy inverse ETF); BUY means cover
    the inverse ETF. HOLD keeps the existing hedge unchanged.
    """

    def __init__(self, fast_period: int = 20, slow_period: int = 50,
                 rsi_period: int = 14, rsi_entry: float = 55.0,
                 rsi_cover: float = 60.0, atr_period: int = 14,
                 min_atr_pct: float = 0.25, max_atr_pct: float = 8.0):
        super().__init__(name=f"Short Regime ({fast_period}/{slow_period}, RSI:{rsi_period})")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.rsi_period = rsi_period
        self.rsi_entry = rsi_entry
        self.rsi_cover = rsi_cover
        self.atr_period = atr_period
        self.min_atr_pct = min_atr_pct
        self.max_atr_pct = max_atr_pct

    def generate_signal(self, df: pd.DataFrame) -> str:
        required = max(self.slow_period, self.rsi_period, self.atr_period) + 3
        if len(df) < required:
            return "HOLD"
        close = pd.to_numeric(df["close"], errors="coerce")
        high = pd.to_numeric(df["high"], errors="coerce")
        low = pd.to_numeric(df["low"], errors="coerce")
        if close.isna().any() or high.isna().any() or low.isna().any():
            return "HOLD"
        fast = close.ewm(span=self.fast_period, adjust=False).mean()
        slow = close.ewm(span=self.slow_period, adjust=False).mean()
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / self.rsi_period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / self.rsi_period, adjust=False).mean()
        rsi = 100 - (100 / (1 + avg_gain / avg_loss.replace(0, 1e-9)))
        prev_close = close.shift(1)
        tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
        atr_pct = (tr.ewm(alpha=1 / self.atr_period, adjust=False).mean() / close) * 100
        values = [fast.iloc[-1], fast.iloc[-2], slow.iloc[-1], slow.iloc[-2], rsi.iloc[-1], rsi.iloc[-2], atr_pct.iloc[-1]]
        if any(pd.isna(v) for v in values):
            return "HOLD"
        trend_down = fast.iloc[-1] < slow.iloc[-1] and close.iloc[-1] < slow.iloc[-1]
        trend_recovered = close.iloc[-1] > slow.iloc[-1] or fast.iloc[-1] > slow.iloc[-1]
        rejection = close.iloc[-2] >= fast.iloc[-2] and close.iloc[-1] < fast.iloc[-1]
        momentum_break = rsi.iloc[-2] > self.rsi_entry >= rsi.iloc[-1]
        volatility_ok = self.min_atr_pct <= atr_pct.iloc[-1] <= self.max_atr_pct
        if trend_down and volatility_ok and (rejection or momentum_break) and 32.0 < rsi.iloc[-1] <= self.rsi_entry:
            return "SELL"
        if trend_recovered or rsi.iloc[-1] >= self.rsi_cover:
            return "BUY"
        return "HOLD"