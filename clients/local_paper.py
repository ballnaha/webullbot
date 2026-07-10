import os
import json
import pandas as pd
import yfinance as yf
from datetime import datetime
from clients.base import BaseTradingClient

class LocalPaperTradingClient(BaseTradingClient):
    """
    Offline simulation client that uses yfinance to fetch market data 
    and saves balance/positions to a local JSON file.
    """

    def __init__(self, initial_cash: float = 10000.0, portfolio_file: str = "local_portfolio.json"):
        self.portfolio_file = portfolio_file
        self.initial_cash = initial_cash
        from config import Config
        self.initial_cash_hkd = Config.SIMULATED_INITIAL_CASH_HKD
        self.bars_cache = {}
        self.price_cache = {}
        self._load_portfolio()

    def _load_portfolio(self):
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                    self.portfolio = json.load(f)
                if "last_prices" not in self.portfolio:
                    self.portfolio["last_prices"] = {}
            except Exception:
                self._init_portfolio()
        else:
            self._init_portfolio()

    def _init_portfolio(self):
        self.portfolio = {
            "balance": {
                "cash": self.initial_cash,
                "currency": "USD",
                "cash_hkd": self.initial_cash_hkd,
                "currency_hkd": "HKD"
            },
            "positions": {}, # Format: { "0700.HK": { "qty": 100, "avg_price": 350.0, "entry_time": "2026-07-10 09:00:00", "peak_price": 350.0 } }
            "transactions": [], # List of transaction logs
            "last_prices": {} # Cache of last known prices
        }
        self._save_portfolio()

    def _migrate_positions(self):
        """Backward-compatible migration: เติม entry_time และ peak_price ให้ positions เดิมที่ยังไม่มีฟิลด์เหล่านี้"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        changed = False
        for symbol, pos in self.portfolio.get("positions", {}).items():
            if "entry_time" not in pos:
                pos["entry_time"] = now_str
                changed = True
            if "peak_price" not in pos:
                pos["peak_price"] = pos.get("avg_price", 0.0)
                changed = True
        if changed:
            self._save_portfolio()

    def _save_portfolio(self):
        with open(self.portfolio_file, 'w', encoding='utf-8') as f:
            json.dump(self.portfolio, f, indent=4, ensure_ascii=False)

    def login(self) -> bool:
        # Local paper trading doesn't need login, always succeeds
        # Run migration on every login to ensure new fields exist
        self._migrate_positions()
        return True

    def get_account_balance(self) -> dict:
        self._load_portfolio()
        cash_usd = self.portfolio["balance"].get("cash", self.initial_cash)
        cash_hkd = self.portfolio["balance"].get("cash_hkd", self.initial_cash * 7.8)
        
        total_mv_usd = 0.0
        total_cost_usd = 0.0
        
        total_mv_hkd = 0.0
        total_cost_hkd = 0.0
        
        for symbol, pos in self.portfolio["positions"].items():
            qty = pos["qty"]
            avg_price = pos["avg_price"]
            
            current_price = self._get_current_price(symbol)
            if current_price <= 0:
                current_price = avg_price
            market_value = qty * current_price
            cost = qty * avg_price
            
            if symbol.upper().endswith(".HK"):
                total_mv_hkd += market_value
                total_cost_hkd += cost
            else:
                total_mv_usd += market_value
                total_cost_usd += cost

        net_liq_usd = cash_usd + total_mv_usd
        unrealized_pnl_usd = total_mv_usd - total_cost_usd

        net_liq_hkd = cash_hkd + total_mv_hkd
        unrealized_pnl_hkd = total_mv_hkd - total_cost_hkd

        return {
            "cash": cash_usd,
            "net_liquidation": net_liq_usd,
            "unrealized_pnl": unrealized_pnl_usd,
            "currency": "USD",
            "cash_hkd": cash_hkd,
            "net_liquidation_hkd": net_liq_hkd,
            "unrealized_pnl_hkd": unrealized_pnl_hkd,
            "currency_hkd": "HKD"
        }

    def get_positions(self) -> list:
        self._load_portfolio()
        positions_list = []
        
        for symbol, pos in self.portfolio["positions"].items():
            qty = pos["qty"]
            avg_price = pos["avg_price"]
            current_price = self._get_current_price(symbol)
            if current_price <= 0:
                current_price = avg_price
            market_value = qty * current_price
            unrealized_pnl = market_value - (qty * avg_price)
            
            positions_list.append({
                "symbol": symbol,
                "qty": qty,
                "avg_price": avg_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl
            })
            
        return positions_list

    def _map_interval(self, interval: str) -> str:
        # Map Webull intervals to yfinance intervals
        mapping = {
            "m1": "1m",
            "m5": "5m",
            "m15": "15m",
            "m30": "30m",
            "h1": "1h",
            "d": "1d"
        }
        return mapping.get(interval.lower(), "5m")

    def get_bars(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        yf_interval = self._map_interval(interval)
        
        # Caching logic to prevent yfinance rate limits
        import time
        cache_key = (symbol, yf_interval)
        # Lifetimes in seconds for interval types
        lifetimes = {
            "1m": 30,
            "5m": 120,
            "15m": 300,
            "30m": 600,
            "1h": 1200,
            "1d": 14400
        }
        lifetime = lifetimes.get(yf_interval, 120)
        
        if cache_key in self.bars_cache:
            cache_time, cached_df = self.bars_cache[cache_key]
            if time.time() - cache_time < lifetime:
                return cached_df
        
        # Determine the period to request based on limit & interval
        if yf_interval in ["1m"]:
            period = "2d"
        elif yf_interval in ["5m", "15m", "30m"]:
            period = "5d"
        elif yf_interval in ["1h"]:
            period = "1mo"
        else:
            period = "6mo"

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=yf_interval)
            
            if df.empty:
                if cache_key in self.bars_cache:
                    return self.bars_cache[cache_key][1]
                return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
                
            # Rename columns to standard lowercase representation
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            # Keep only standard columns and take the last 'limit' items
            df = df[['open', 'high', 'low', 'close', 'volume']].tail(limit)
            
            # Save to cache
            self.bars_cache[cache_key] = (time.time(), df)
            return df
        except Exception as e:
            # Fallback to stale cached bars on error/rate limit
            print(f"Error fetching data from yfinance for {symbol}: {e}")
            if cache_key in self.bars_cache:
                print(f"Returning stale cached data for {symbol} due to rate limiting/error.")
                return self.bars_cache[cache_key][1]
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

    def _update_last_price(self, symbol: str, price: float):
        if "last_prices" not in self.portfolio:
            self.portfolio["last_prices"] = {}
        if self.portfolio["last_prices"].get(symbol) != price:
            self.portfolio["last_prices"][symbol] = price
            self._save_portfolio()

    def _get_current_price(self, symbol: str) -> float:
        import time
        # Check local client price cache first (lifetime: 10 seconds)
        if symbol in self.price_cache:
            cache_time, price = self.price_cache[symbol]
            if time.time() - cache_time < 10:
                return price

        try:
            ticker = yf.Ticker(symbol)
            
            # Try fast_info first (extremely fast and doesn't download historical tables)
            try:
                val = ticker.fast_info.get('last_price')
                if val is not None and val > 0:
                    price = float(val)
                    self._update_last_price(symbol, price)
                    self.price_cache[symbol] = (time.time(), price)
                    return price
            except Exception:
                pass
                
            # Fallback to history to get last close
            df = ticker.history(period="1d", interval="1m")
            if not df.empty:
                price = float(df['Close'].iloc[-1])
                self._update_last_price(symbol, price)
                self.price_cache[symbol] = (time.time(), price)
                return price
            
            # Fallback to daily
            df = ticker.history(period="5d", interval="1d")
            if not df.empty:
                price = float(df['Close'].iloc[-1])
                self._update_last_price(symbol, price)
                self.price_cache[symbol] = (time.time(), price)
                return price
        except Exception:
            pass
            
        # Return last known price if yfinance fails
        self._load_portfolio()
        last_prices = self.portfolio.get("last_prices", {})
        if symbol in last_prices and last_prices[symbol] > 0:
            price = float(last_prices[symbol])
            self.price_cache[symbol] = (time.time(), price)
            return price
            
        return 0.0

    def place_order(self, symbol: str, qty: int, action: str, order_type: str = "MKT", price: float = None) -> dict:
        self._load_portfolio()
        symbol = symbol.upper()
        action = action.upper()
        
        current_price = price if (order_type.upper() == "LMT" and price is not None) else self._get_current_price(symbol)
        
        if current_price <= 0:
            return {
                "status": "FAILED",
                "reason": f"Could not determine price for {symbol}"
            }

        is_hk = symbol.endswith(".HK")
        total_cost = current_price * qty
        cash_usd = self.portfolio["balance"].get("cash", self.initial_cash)
        cash_hkd = self.portfolio["balance"].get("cash_hkd", self.initial_cash * 7.8)
        
        cash = cash_hkd if is_hk else cash_usd
        currency_label = "HKD" if is_hk else "USD"

        if action == "BUY":
            if cash < total_cost:
                return {
                    "status": "FAILED",
                    "reason": f"Insufficient funds. Required: {total_cost:.2f} {currency_label}, Available: {cash:.2f} {currency_label}"
                }
            
            # Deduct cash
            if is_hk:
                self.portfolio["balance"]["cash_hkd"] = cash_hkd - total_cost
                self.portfolio["balance"]["cash"] = cash_usd - (total_cost / 7.8)
            else:
                self.portfolio["balance"]["cash"] = cash_usd - total_cost
                self.portfolio["balance"]["cash_hkd"] = cash_hkd - (total_cost * 7.8)
            
            # Update position
            pos = self.portfolio["positions"].get(symbol, {"qty": 0, "avg_price": 0.0})
            prev_qty = pos["qty"]
            prev_avg = pos["avg_price"]
            
            new_qty = prev_qty + qty
            new_avg = ((prev_qty * prev_avg) + total_cost) / new_qty
            
            self.portfolio["positions"][symbol] = {
                "qty": new_qty,
                "avg_price": new_avg,
                "entry_time": pos.get("entry_time") if prev_qty > 0 else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "peak_price": pos.get("peak_price", new_avg) if prev_qty > 0 else new_avg,
            }
            
        elif action == "SELL":
            pos = self.portfolio["positions"].get(symbol, {"qty": 0, "avg_price": 0.0})
            if pos["qty"] < qty:
                return {
                    "status": "FAILED",
                    "reason": f"Insufficient shares. Required: {qty}, Owned: {pos['qty']}"
                }
                
            # Add to cash
            if is_hk:
                self.portfolio["balance"]["cash_hkd"] = cash_hkd + total_cost
                self.portfolio["balance"]["cash"] = cash_usd + (total_cost / 7.8)
            else:
                self.portfolio["balance"]["cash"] = cash_usd + total_cost
                self.portfolio["balance"]["cash_hkd"] = cash_hkd + (total_cost * 7.8)
            
            # Update position
            pos["qty"] -= qty
            if pos["qty"] == 0:
                del self.portfolio["positions"][symbol]
            else:
                self.portfolio["positions"][symbol] = pos
        else:
            return {
                "status": "FAILED",
                "reason": f"Invalid action: {action}"
            }

        # Log transaction
        tx = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "action": action,
            "qty": qty,
            "price": current_price,
            "total": total_cost
        }
        self.portfolio["transactions"].append(tx)
        self._save_portfolio()
        
        return {
            "status": "FILLED",
            "order_id": f"sim-{int(datetime.now().timestamp())}",
            "symbol": symbol,
            "action": action,
            "qty": qty,
            "price": current_price,
            "total": total_cost
        }

    def get_working_orders(self) -> list:
        # In Local Paper simulation, orders are filled instantly, so there are no working orders
        return []
