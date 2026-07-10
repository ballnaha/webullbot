import pandas as pd
from strategies.base import BaseStrategy

class VolumeEmaBreakoutStrategy(BaseStrategy):
    """
    Volume Spike + EMA Breakout Strategy.
    Generates a BUY signal when:
      - Fast EMA (9) crosses above Slow EMA (21) AND
      - Current volume is higher than (vol_factor * vol_sma20), signifying a strong breakout.
    Generates a SELL signal when:
      - Fast EMA (9) crosses below Slow EMA (21) OR
      - Current close price falls below Slow EMA (21).
    """

    def __init__(self, fast_period: int = 9, slow_period: int = 21, vol_period: int = 20, vol_factor: float = 2.5):
        super().__init__(name=f"Volume+EMA Breakout ({fast_period}/{slow_period}, Vol:{vol_period} x{vol_factor})")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.vol_period = vol_period
        self.vol_factor = vol_factor

    def generate_signal(self, df: pd.DataFrame) -> str:
        required_len = max(self.slow_period, self.vol_period) + 3
        if len(df) < required_len:
            return "HOLD"

        close = df['close']
        volume = df['volume']

        # 1. Calculate EMAs
        ema_fast = close.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow_period, adjust=False).mean()

        # 2. Calculate Volume SMA
        vol_sma = volume.rolling(window=self.vol_period).mean()

        # Check last two values for crossovers
        fast_curr = ema_fast.iloc[-1]
        fast_prev = ema_fast.iloc[-2]
        slow_curr = ema_slow.iloc[-1]
        slow_prev = ema_slow.iloc[-2]
        
        vol_curr = volume.iloc[-1]
        vol_limit = vol_sma.iloc[-1] * self.vol_factor
        c_price = float(close.iloc[-1])

        if pd.isna(fast_curr) or pd.isna(fast_prev) or pd.isna(slow_curr) or pd.isna(slow_prev) or pd.isna(vol_limit):
            return "HOLD"

        # Signal triggers
        golden_cross = (fast_prev <= slow_prev) and (fast_curr > slow_curr)
        death_cross = (fast_prev >= slow_prev) and (fast_curr < slow_curr)
        volume_spike = vol_curr > vol_limit
        below_ema_slow = c_price < slow_curr

        # BUY trigger: Golden Cross + Volume Spike confirmation
        if golden_cross and volume_spike:
            return "BUY"

        # SELL trigger: Death Cross OR price drops below EMA slow
        elif death_cross or below_ema_slow:
            return "SELL"

        return "HOLD"
