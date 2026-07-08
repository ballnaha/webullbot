from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """
    Abstract Base Class for all trading strategies.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> str:
        """
        Analyze price data and generate a trading signal.
        Args:
            df (pd.DataFrame): Historical bar data with columns ['open', 'high', 'low', 'close', 'volume'].
        Returns:
            str: "BUY", "SELL", or "HOLD"
        """
        pass
