from abc import ABC, abstractmethod
import pandas as pd

class BaseTradingClient(ABC):
    """
    Abstract Base Class for all trading clients (Simulation and Real Webull APIs).
    """

    @abstractmethod
    def login(self) -> bool:
        """
        Authenticate with the trading provider.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_account_balance(self) -> dict:
        """
        Retrieve account balance information.
        Returns:
            dict: {
                "cash": float,            # Available cash to trade
                "net_liquidation": float, # Total account value (cash + positions)
                "unrealized_pnl": float,  # Total unrealized profit/loss
                "currency": str           # e.g., "USD"
            }
        """
        pass

    @abstractmethod
    def get_positions(self) -> list:
        """
        Retrieve current open positions.
        Returns:
            list of dicts: [
                {
                    "symbol": str,
                    "qty": int,
                    "avg_price": float,
                    "market_value": float,
                    "unrealized_pnl": float
                },
                ...
            ]
        """
        pass

    @abstractmethod
    def get_bars(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """
        Retrieve historical bar (candlestick) data.
        Args:
            symbol (str): Ticker symbol.
            interval (str): Time interval (m1, m5, m15, m30, h1, d).
            limit (int): Number of bars to retrieve.
        Returns:
            pd.DataFrame: Columns ['open', 'high', 'low', 'close', 'volume'] indexed by Datetime.
        """
        pass

    @abstractmethod
    def place_order(self, symbol: str, qty: int, action: str, order_type: str = "MKT", price: float = None) -> dict:
        """
        Place a buy or sell order.
        Args:
            symbol (str): Ticker symbol.
            qty (int): Quantity of shares.
            action (str): "BUY" or "SELL".
            order_type (str): "MKT" (Market) or "LMT" (Limit).
            price (float): Order price (required for Limit orders).
        Returns:
            dict: Order receipt detailing status, order ID, etc.
        """
        pass

    @abstractmethod
    def get_working_orders(self) -> list:
        """
        Retrieve list of working (pending) orders.
        Returns:
            list of dicts.
        """
        pass
