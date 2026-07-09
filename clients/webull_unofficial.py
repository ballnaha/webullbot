import pandas as pd
from datetime import datetime
from clients.base import BaseTradingClient

class WebullUnofficialClient(BaseTradingClient):
    """
    Client for interacting with Webull using the unofficial 'webull' Python library.
    Supports both paper trading (via paper_webull) and live trading (via webull).
    """

    def __init__(self, username, password, trade_pin=None, is_paper=True, device_name="PythonBot"):
        self.username = username
        self.password = password
        self.trade_pin = trade_pin
        self.is_paper = is_paper
        self.device_name = device_name
        self.wb = None
        self._init_sdk()

    def _init_sdk(self):
        try:
            if self.is_paper:
                from webull.webull import paper_webull
                self.wb = paper_webull()
            else:
                from webull.webull import webull
                self.wb = webull()
        except ImportError as e:
            raise ImportError(
                f"The unofficial 'webull' package is not installed or import failed: {e}. "
                "Please run 'pip install webull' to use this client."
            )

    def login(self) -> bool:
        print(f"Logging in to Webull Unofficial API ({'Paper' if self.is_paper else 'Live'})...")
        try:
            # First try a simple login. If Webull prompts for MFA, this might throw or require extra steps.
            # In the current webull library, login returns a dict.
            login_result = self.wb.login(self.username, self.password, self.device_name)
            
            # Check if MFA is required (often indicated by a need for verification code)
            # Depending on webull library updates, we might need to handle this.
            if isinstance(login_result, dict) and login_result.get('code') == 'MFA_REQUIRED':
                print("MFA (Multi-Factor Authentication) is required!")
                # For console interactive prompt
                mfa_code = input("Please enter the MFA code sent to your phone/email: ")
                login_result = self.wb.login(self.username, self.password, self.device_name, mfa_code)

            # Check if login was successful
            # The library typically sets credentials internally, let's verify by retrieving account ID or checking response
            account_id = None
            try:
                if self.is_paper:
                    # In paper trading, we might have multiple paper accounts or default to one
                    accounts = self.wb.get_account()
                    if accounts:
                        account_id = accounts[0].get('accountKey')
                else:
                    account_id = self.wb.get_account_id()
            except Exception:
                pass

            if not account_id and not self.is_paper:
                print("Failed to retrieve Account ID. Check your credentials.")
                return False

            # If live trading, we must unlock trade token using PIN
            if not self.is_paper:
                if not self.trade_pin:
                    print("Error: Trade PIN is required for Live trading!")
                    return False
                print("Unlocking trade token using PIN...")
                trade_token_ok = self.wb.get_trade_token(self.trade_pin)
                if not trade_token_ok:
                    print("Warning: Failed to set trade token. You may not be able to place trades.")

            print("Webull Unofficial API login successful!")
            return True

        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def get_account_balance(self) -> dict:
        try:
            if self.is_paper:
                # Retrieve paper account details
                portfolio = self.wb.get_portfolio()
                # Portfolio is often a list or dict of account balances
                # Let's parse safely
                cash = float(portfolio.get('usableCash', 0.0))
                net_liquidation = float(portfolio.get('totalAssetValue', 0.0))
                unrealized_pnl = float(portfolio.get('unrealizedProfitLoss', 0.0))
            else:
                # Live account
                acct = self.wb.get_account()
                # acct contains list of details
                # Let's extract values
                account_data = acct.get('accountMembers', {})
                cash = float(account_data.get('usableCash', 0.0))
                net_liquidation = float(account_data.get('netLiquidationValue', 0.0))
                unrealized_pnl = float(account_data.get('unrealizedProfitLoss', 0.0))

            return {
                "cash": cash,
                "net_liquidation": net_liquidation,
                "unrealized_pnl": unrealized_pnl,
                "currency": "USD"
            }
        except Exception as e:
            print(f"Error fetching account balance: {e}")
            return {"cash": 0.0, "net_liquidation": 0.0, "unrealized_pnl": 0.0, "currency": "USD"}

    def get_positions(self) -> list:
        try:
            positions_list = []
            positions_data = []
            
            if self.is_paper:
                positions_data = self.wb.get_positions()
            else:
                acct = self.wb.get_account()
                positions_data = acct.get('positions', [])

            for pos in positions_data:
                # Standardize keys
                ticker = pos.get('ticker', {})
                symbol = ticker.get('symbol', 'UNKNOWN')
                qty = int(pos.get('position', 0))
                avg_price = float(pos.get('costPrice', 0.0))
                market_value = float(pos.get('marketValue', 0.0))
                unrealized_pnl = float(pos.get('unrealizedProfitLoss', 0.0))

                positions_list.append({
                    "symbol": symbol,
                    "qty": qty,
                    "avg_price": avg_price,
                    "market_value": market_value,
                    "unrealized_pnl": unrealized_pnl
                })
            return positions_list
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return []

    def get_bars(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """
        Get bars from Webull. 
        Webull intervals: m1, m5, m15, m30, h1, d (mapped to Webull API standards: 1, 5, 15, 30, 60, d)
        """
        # Map to unofficial SDK standard interval representation
        # 'd' for day, numbers (in minutes) for intraday
        mapping = {
            "m1": "1",
            "m5": "5",
            "m15": "15",
            "m30": "30",
            "h1": "60",
            "d": "d"
        }
        wb_interval = mapping.get(interval.lower(), "5")
        
        try:
            # get_bars takes parameters like: stock, interval, count
            data = self.wb.get_bars(stock=symbol, interval=wb_interval, count=limit)
            
            if not isinstance(data, list) or len(data) == 0:
                # Webull API sometimes returns raw df or empty dict
                if isinstance(data, pd.DataFrame):
                    df = data
                else:
                    return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
            else:
                # Create DataFrame from list of dicts
                df = pd.DataFrame(data)

            if df.empty:
                return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

            # Webull bars typically contain fields: open, high, low, close, volume, datetime
            # Standardize column casing
            df = df.rename(columns={
                'Open': 'open', 'open': 'open',
                'High': 'high', 'high': 'high',
                'Low': 'low', 'low': 'low',
                'Close': 'close', 'close': 'close',
                'Volume': 'volume', 'volume': 'volume'
            })
            
            # Extract standard columns
            df = df[['open', 'high', 'low', 'close', 'volume']]
            return df
        except Exception as e:
            print(f"Error fetching historical bars for {symbol}: {e}")
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

    def place_order(self, symbol: str, qty: int, action: str, order_type: str = "MKT", price: float = None) -> dict:
        """
        Place buy/sell order.
        For Webull, orderType can be 'MKT' or 'LMT'.
        """
        symbol = symbol.upper()
        action = action.upper() # BUY or SELL
        order_type = order_type.upper() # MKT or LMT
        
        # Webull action parameter typically matches BUY or SELL
        # Order types: MKT, LMT
        try:
            if self.is_paper:
                # For paper trading
                # place_order arguments: stock, price, qty, action, orderType
                res = self.wb.place_order(
                    stock=symbol,
                    price=price if order_type == "LMT" else 0.0,
                    qty=qty,
                    action=action,
                    orderType=order_type
                )
            else:
                # For live trading
                res = self.wb.place_order(
                    stock=symbol,
                    price=price if order_type == "LMT" else 0.0,
                    qty=qty,
                    action=action,
                    orderType=order_type
                )
            
            # Parse response
            # Typically returns a dictionary like {"orderId": "...", "success": True}
            if isinstance(res, dict) and (res.get('success') or 'orderId' in res):
                return {
                    "status": "SUBMITTED",
                    "order_id": res.get('orderId', 'unknown'),
                    "symbol": symbol,
                    "action": action,
                    "qty": qty,
                    "price": price or "MKT",
                    "raw": res
                }
            else:
                return {
                    "status": "FAILED",
                    "reason": str(res)
                }
        except Exception as e:
            print(f"Error placing order: {e}")
            return {
                "status": "FAILED",
                "reason": str(e)
            }

    def get_working_orders(self) -> list:
        try:
            # Get pending orders
            # Usually returns a list of orders
            orders = self.wb.get_current_orders()
            working = []
            for order in orders:
                status = order.get('status', '').upper()
                if status in ['SUBMITTED', 'PENDING', 'WORKING', 'PARTIALLY_FILLED']:
                    working.append({
                        "order_id": order.get('orderId'),
                        "symbol": order.get('ticker', {}).get('symbol'),
                        "action": order.get('action'),
                        "qty": order.get('quantity'),
                        "price": order.get('price'),
                        "status": status
                    })
            return working
        except Exception as e:
            print(f"Error fetching working orders: {e}")
            return []
