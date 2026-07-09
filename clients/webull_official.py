import pandas as pd
import yfinance as yf
from clients.base import BaseTradingClient

class WebullOfficialClient(BaseTradingClient):
    """
    Client for interacting with Webull using the official OpenAPI SDK.
    Requires App Key and App Secret.
    """

    def __init__(self, app_key: str, app_secret: str, region: str = "us", endpoint: str = None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.region = region
        self.endpoint = endpoint
        self.api_client = None
        self.trade_client = None
        self.account_id = None
        self._init_sdk()

    def _init_sdk(self):
        try:
            from webull.core.client import ApiClient
            from webull.trade.trade_client import TradeClient
            
            # Setup API client
            self.api_client = ApiClient(self.app_key, self.app_secret, self.region)
            if self.endpoint:
                self.api_client.add_endpoint(self.region, self.endpoint)
                
            self.trade_client = TradeClient(self.api_client)
        except ImportError:
            raise ImportError(
                "The official 'webull-openapi-python-sdk' is not installed. "
                "Please run 'pip install webull-openapi-python-sdk' to use this client."
            )

    def login(self) -> bool:
        print(f"Logging in to Webull Official OpenAPI ({self.region})...")
        try:
            # Get account list to verify credentials and extract account ID
            res = self.trade_client.account_v2.get_account_list()
            if res.status_code == 200:
                accounts = res.json()
                if accounts and len(accounts) > 0:
                    # Retrieve first account ID
                    self.account_id = accounts[0].get('accountId')
                    print(f"Official OpenAPI login successful! Account ID: {self.account_id}")
                    return True
                else:
                    print("Error: No accounts found for these OpenAPI credentials.")
                    return False
            else:
                print(f"Failed to login: {res.status_code} - {res.text}")
                return False
        except Exception as e:
            print(f"Error logging in via Official OpenAPI: {e}")
            return False

    def get_account_balance(self) -> dict:
        if not self.account_id:
            return {"cash": 0.0, "net_liquidation": 0.0, "unrealized_pnl": 0.0, "currency": "USD"}
            
        try:
            res = self.trade_client.account_v2.get_account_balance(account_id=self.account_id)
            if res.status_code == 200:
                data = res.json()
                # Parse standard fields from Official API json response
                cash = float(data.get('cashBalance', 0.0))
                net_liquidation = float(data.get('netLiquidationValue', 0.0))
                unrealized_pnl = float(data.get('unrealizedPnL', 0.0))
                currency = data.get('currency', 'USD')
                
                return {
                    "cash": cash,
                    "net_liquidation": net_liquidation,
                    "unrealized_pnl": unrealized_pnl,
                    "currency": currency
                }
            else:
                print(f"Failed to fetch balance: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Error fetching balance from OpenAPI: {e}")
            
        return {"cash": 0.0, "net_liquidation": 0.0, "unrealized_pnl": 0.0, "currency": "USD"}

    def get_positions(self) -> list:
        if not self.account_id:
            return []
            
        try:
            res = self.trade_client.account_v2.get_positions(account_id=self.account_id)
            if res.status_code == 200:
                positions_data = res.json()
                positions_list = []
                for pos in positions_data:
                    positions_list.append({
                        "symbol": pos.get('symbol', '').upper(),
                        "qty": int(pos.get('positionQty', 0)),
                        "avg_price": float(pos.get('costPrice', 0.0)),
                        "market_value": float(pos.get('marketValue', 0.0)),
                        "unrealized_pnl": float(pos.get('unrealizedPnL', 0.0))
                    })
                return positions_list
            else:
                print(f"Failed to fetch positions: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Error fetching positions from OpenAPI: {e}")
            
        return []

    def get_bars(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """
        Retrieves historical bars.
        As Webull OpenAPI historical market data requires specific real-time/historical data subscriptions,
        we use yfinance as a reliable, free fallback to avoid errors.
        """
        # Map Webull interval to yfinance
        mapping = {
            "m1": "1m", "m5": "5m", "m15": "15m", "m30": "30m", "h1": "1h", "d": "1d"
        }
        yf_interval = mapping.get(interval.lower(), "5m")
        period = "5d" if "m" in interval else "6mo"
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=yf_interval)
            if df.empty:
                return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
                
            df = df.rename(columns={
                'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
            })
            df = df[['open', 'high', 'low', 'close', 'volume']].tail(limit)
            return df
        except Exception as e:
            print(f"Error retrieving market data (yfinance fallback) for {symbol}: {e}")
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

    def place_order(self, symbol: str, qty: int, action: str, order_type: str = "MKT", price: float = None) -> dict:
        if not self.account_id:
            return {"status": "FAILED", "reason": "No authenticated account"}
            
        symbol = symbol.upper()
        action = action.upper() # BUY or SELL
        order_type = order_type.upper() # MKT or LMT
        
        try:
            # Formulate order request payload
            # Official SDK order placement method
            res = self.trade_client.order_v2.place_order(
                account_id=self.account_id,
                symbol=symbol,
                qty=qty,
                action=action,
                order_type=order_type,
                price=price if order_type == "LMT" else None
            )
            
            if res.status_code == 200:
                data = res.json()
                return {
                    "status": "SUBMITTED",
                    "order_id": data.get('orderId'),
                    "symbol": symbol,
                    "action": action,
                    "qty": qty,
                    "price": price or "MKT",
                    "raw": data
                }
            else:
                return {
                    "status": "FAILED",
                    "reason": f"{res.status_code} - {res.text}"
                }
        except Exception as e:
            print(f"Error placing order via OpenAPI: {e}")
            return {"status": "FAILED", "reason": str(e)}

    def get_working_orders(self) -> list:
        if not self.account_id:
            return []
            
        try:
            res = self.trade_client.order_v2.get_orders(account_id=self.account_id, status="WORKING")
            if res.status_code == 200:
                orders_data = res.json()
                working = []
                for order in orders_data:
                    working.append({
                        "order_id": order.get('orderId'),
                        "symbol": order.get('symbol'),
                        "action": order.get('action'),
                        "qty": order.get('qty'),
                        "price": order.get('price'),
                        "status": order.get('status')
                    })
                return working
        except Exception as e:
            print(f"Error fetching orders from OpenAPI: {e}")
            
        return []
