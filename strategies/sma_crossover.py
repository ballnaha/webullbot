import pandas as pd
from strategies.base import BaseStrategy

class SMACrossoverStrategy(BaseStrategy):
    """
    Simple Moving Average (SMA) Crossover Strategy.
    Generates a BUY signal when a fast SMA crosses above a slow SMA.
    Generates a SELL signal when a fast SMA crosses below a slow SMA.
    """

    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        super().__init__(name=f"SMA Crossover ({fast_period}/{slow_period})")
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signal(self, df: pd.DataFrame) -> str:
        # Check if we have enough data points
        required_len = self.slow_period + 2
        if len(df) < required_len:
            return "HOLD"

        # Calculate SMAs
        close = df['close']
        sma_fast = close.rolling(window=self.fast_period).mean()
        sma_slow = close.rolling(window=self.slow_period).mean()

        # Check last two values to detect a crossover
        # Index -1 is the most recent closed candle, Index -2 is the previous candle
        fast_curr = sma_fast.iloc[-1]
        fast_prev = sma_fast.iloc[-2]
        slow_curr = sma_slow.iloc[-1]
        slow_prev = sma_slow.iloc[-2]

        # Handle NaNs
        if pd.isna(fast_curr) or pd.isna(fast_prev) or pd.isna(slow_curr) or pd.isna(slow_prev):
            return "HOLD"

        # Golden Cross (Fast crosses above Slow)
        if fast_prev <= slow_prev and fast_curr > slow_curr:
            return "BUY"
            
        # Death Cross (Fast crosses below Slow)
        elif fast_prev >= slow_prev and fast_curr < slow_curr:
            return "SELL"

        return "HOLD"
