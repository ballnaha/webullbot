import pandas as pd
from strategies.base import BaseStrategy

class SmaRsiHybridStrategy(BaseStrategy):
    """
    SMA + RSI Hybrid Strategy.
    Generates a BUY signal when:
      - Golden Cross occurs (Fast SMA crosses above Slow SMA) AND RSI is not overbought (< 60).
      - OR RSI crosses back above oversold threshold (40) AND Fast SMA is already above Slow SMA.
    Generates a SELL signal when:
      - Death Cross occurs (Fast SMA crosses below Slow SMA).
      - OR RSI crosses back below overbought threshold (60).
    """

    def __init__(self, fast_period: int = 10, slow_period: int = 30, rsi_period: int = 14, oversold: float = 40.0, overbought: float = 60.0):
        super().__init__(name=f"SMA+RSI Hybrid ({fast_period}/{slow_period}, RSI:{rsi_period})")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signal(self, df: pd.DataFrame) -> str:
        required_len = max(self.slow_period, self.rsi_period) + 3
        if len(df) < required_len:
            return "HOLD"

        close = df['close']
        
        # 1. Calculate SMAs
        sma_fast = close.rolling(window=self.fast_period).mean()
        sma_slow = close.rolling(window=self.slow_period).mean()
        
        # 2. Calculate RSI
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/self.rsi_period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/self.rsi_period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-9)
        rsi = 100 - (100 / (1 + rs))

        # Check last two values for crossovers
        fast_curr = sma_fast.iloc[-1]
        fast_prev = sma_fast.iloc[-2]
        slow_curr = sma_slow.iloc[-1]
        slow_prev = sma_slow.iloc[-2]
        
        rsi_curr = rsi.iloc[-1]
        rsi_prev = rsi.iloc[-2]

        if pd.isna(fast_curr) or pd.isna(fast_prev) or pd.isna(slow_curr) or pd.isna(slow_prev) or pd.isna(rsi_curr) or pd.isna(rsi_prev):
            return "HOLD"

        # Signal Triggers
        # Golden Cross check
        golden_cross = (fast_prev <= slow_prev) and (fast_curr > slow_curr)
        # Death Cross check
        death_cross = (fast_prev >= slow_prev) and (fast_curr < slow_curr)
        
        # RSI Cross checks
        rsi_exiting_oversold = (rsi_prev < self.oversold) and (rsi_curr >= self.oversold)
        rsi_exiting_overbought = (rsi_prev > self.overbought) and (rsi_curr <= self.overbought)

        # BUY trigger:
        # 1. Golden Cross AND RSI is below overbought (not too expensive)
        # 2. OR RSI crosses above oversold AND Fast SMA is already above Slow SMA
        if (golden_cross and rsi_curr < self.overbought) or (rsi_exiting_oversold and fast_curr > slow_curr):
            return "BUY"

        # SELL trigger:
        # 1. Death Cross
        # 2. OR RSI crosses below overbought
        elif death_cross or rsi_exiting_overbought:
            return "SELL"

        return "HOLD"
