import pandas as pd
from strategies.base import BaseStrategy


class RegimeAdaptiveStrategy(BaseStrategy):
    """Trend-following pullback strategy with volatility and RSI filters.

    It enters only when the fast EMA is above the slow EMA, price reclaims the
    fast EMA after a pullback, and momentum is neither oversold nor overbought.
    It exits when the trend regime is lost or downside momentum confirms.
    """

    def __init__(self, fast_period: int = 20, slow_period: int = 50,
                 rsi_period: int = 14, rsi_entry: float = 45.0,
                 rsi_exit: float = 40.0, rsi_ceiling: float = 68.0,
                 atr_period: int = 14, min_atr_pct: float = 0.25,
                 max_atr_pct: float = 8.0):
        super().__init__(name=f"Regime Adaptive ({fast_period}/{slow_period}, RSI:{rsi_period})")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.rsi_period = rsi_period
        self.rsi_entry = rsi_entry
        self.rsi_exit = rsi_exit
        self.rsi_ceiling = rsi_ceiling
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

        ema_fast = close.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow_period, adjust=False).mean()
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / self.rsi_period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / self.rsi_period, adjust=False).mean()
        rsi = 100 - (100 / (1 + avg_gain / avg_loss.replace(0, 1e-9)))

        prev_close = close.shift(1)
        true_range = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
        atr = true_range.ewm(alpha=1 / self.atr_period, adjust=False).mean()
        atr_pct = (atr / close) * 100

        values = [ema_fast.iloc[-1], ema_fast.iloc[-2], ema_slow.iloc[-1],
                  ema_slow.iloc[-2], rsi.iloc[-1], rsi.iloc[-2], atr_pct.iloc[-1]]
        if any(pd.isna(value) for value in values):
            return "HOLD"

        trend_up = ema_fast.iloc[-1] > ema_slow.iloc[-1] and close.iloc[-1] > ema_slow.iloc[-1]
        trend_lost = close.iloc[-1] < ema_slow.iloc[-1] or ema_fast.iloc[-1] < ema_slow.iloc[-1]
        reclaim_fast = close.iloc[-2] <= ema_fast.iloc[-2] and close.iloc[-1] > ema_fast.iloc[-1]
        rsi_reclaim = rsi.iloc[-2] < self.rsi_entry <= rsi.iloc[-1]
        volatility_ok = self.min_atr_pct <= atr_pct.iloc[-1] <= self.max_atr_pct

        if trend_up and volatility_ok and (reclaim_fast or rsi_reclaim) and self.rsi_entry <= rsi.iloc[-1] < self.rsi_ceiling:
            return "BUY"
        if trend_lost or rsi.iloc[-1] < self.rsi_exit:
            return "SELL"
        return "HOLD"