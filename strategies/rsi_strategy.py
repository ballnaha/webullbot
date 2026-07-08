import pandas as pd
from strategies.base import BaseStrategy

class RSIStrategy(BaseStrategy):
    """
    Relative Strength Index (RSI) Trading Strategy.
    Generates a BUY signal when RSI crosses back ABOVE the oversold threshold (default 30).
    Generates a SELL signal when RSI crosses back BELOW the overbought threshold (default 70).
    """

    def __init__(self, period: int = 14, oversold: float = 30.0, overbought: float = 70.0):
        super().__init__(name=f"RSI Strategy ({period}, OS:{oversold}/OB:{overbought})")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signal(self, df: pd.DataFrame) -> str:
        required_len = self.period + 3
        if len(df) < required_len:
            return "HOLD"

        close = df['close']
        
        # Calculate Wilder's RSI
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        # Wilder's smoothing uses alpha = 1 / period
        avg_gain = gain.ewm(alpha=1/self.period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/self.period, adjust=False).mean()
        
        # Avoid division by zero
        rs = avg_gain / avg_loss.replace(0, 1e-9)
        rsi = 100 - (100 / (1 + rs))

        # Check last two values
        rsi_curr = rsi.iloc[-1]
        rsi_prev = rsi.iloc[-2]

        if pd.isna(rsi_curr) or pd.isna(rsi_prev):
            return "HOLD"

        # Signal when exiting the oversold zone (Bullish)
        if rsi_prev < self.oversold and rsi_curr >= self.oversold:
            return "BUY"
            
        # Signal when exiting the overbought zone (Bearish)
        elif rsi_prev > self.overbought and rsi_curr <= self.overbought:
            return "SELL"

        return "HOLD"
