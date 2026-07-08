import time
import pandas as pd
from datetime import datetime
from config import Config
from clients.base import BaseTradingClient
from strategies.base import BaseStrategy

class TradingBot:
    """
    The main coordinator for the trading bot.
    Fetches market data, executes strategy signals, and places trades.
    """

    def __init__(self, client: BaseTradingClient, strategy: BaseStrategy, symbols: list = None):
        self.client = client
        self.strategy = strategy
        self.symbols = symbols or Config.DEFAULT_SYMBOLS
        self.trade_qty = Config.TRADE_QUANTITY
        self.candle_period = Config.CANDLE_PERIOD
        
        # Log lists
        self.logs = []
        self.trades_history = []
        
        self.add_log("Bot initialized with strategy: " + strategy.name)
        self.add_log(f"Monitoring symbols: {', '.join(self.symbols)}")

    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        self.logs.append(formatted_msg)
        # Keep logs list size reasonable
        if len(self.logs) > 100:
            self.logs.pop(0)
        print(formatted_msg) # Fallback console output

    def run_once(self) -> dict:
        """
        Executes one iteration of the trading loop.
        Fetches data, checks signals, and executes orders.
        Returns account summary for display.
        """
        self.add_log("Starting trading loop iteration...")
        
        try:
            # 1. Fetch account info
            balance = self.client.get_account_balance()
            positions = self.client.get_positions()
            
            # Map positions for quick lookup by symbol
            pos_map = {pos['symbol']: pos for pos in positions}
            
            # 2. Iterate through each symbol
            for symbol in self.symbols:
                self.add_log(f"Analyzing {symbol}...")
                
                # Fetch historical price data
                # We fetch 100 bars (more than enough for 14-period RSI or 30-period SMA)
                df = self.client.get_bars(symbol=symbol, interval=self.candle_period, limit=100)
                
                if df.empty:
                    self.add_log(f"Warning: No historical data received for {symbol}. Skipping.")
                    continue
                    
                current_price = float(df['close'].iloc[-1])
                self.add_log(f"Current price for {symbol}: ${current_price:.2f}")
                
                # Generate signal from strategy
                signal = self.strategy.generate_signal(df)
                self.add_log(f"Strategy signal for {symbol}: {signal}")
                
                # 3. Handle signal execution
                owned_position = pos_map.get(symbol)
                owned_qty = owned_position['qty'] if owned_position else 0
                
                if signal == "BUY":
                    if owned_qty > 0:
                        self.add_log(f"Signal is BUY but already own {owned_qty} shares of {symbol}. Skipping.")
                    else:
                        self.add_log(f"Signal: BUY {self.trade_qty} shares of {symbol}...")
                        order_res = self.client.place_order(
                            symbol=symbol,
                            qty=self.trade_qty,
                            action="BUY",
                            order_type="MKT"
                        )
                        
                        if order_res.get("status") in ["FILLED", "SUBMITTED"]:
                            exec_price = order_res.get("price", current_price)
                            self.add_log(f"SUCCESS: Bought {self.trade_qty} shares of {symbol} at ${exec_price:.2f}")
                            self.trades_history.append({
                                "time": datetime.now().strftime("%H:%M:%S"),
                                "symbol": symbol,
                                "action": "BUY",
                                "qty": self.trade_qty,
                                "price": exec_price,
                                "status": order_res.get("status")
                            })
                        else:
                            self.add_log(f"FAILED to place BUY order for {symbol}: {order_res.get('reason', 'Unknown reason')}")
                            
                elif signal == "SELL":
                    if owned_qty <= 0:
                        self.add_log(f"Signal is SELL but do not own any shares of {symbol}. Skipping.")
                    else:
                        self.add_log(f"Signal: SELL {owned_qty} shares of {symbol}...")
                        order_res = self.client.place_order(
                            symbol=symbol,
                            qty=owned_qty,
                            action="SELL",
                            order_type="MKT"
                        )
                        
                        if order_res.get("status") in ["FILLED", "SUBMITTED"]:
                            exec_price = order_res.get("price", current_price)
                            self.add_log(f"SUCCESS: Sold {owned_qty} shares of {symbol} at ${exec_price:.2f}")
                            self.trades_history.append({
                                "time": datetime.now().strftime("%H:%M:%S"),
                                "symbol": symbol,
                                "action": "SELL",
                                "qty": owned_qty,
                                "price": exec_price,
                                "status": order_res.get("status")
                            })
                        else:
                            self.add_log(f"FAILED to place SELL order for {symbol}: {order_res.get('reason', 'Unknown reason')}")
                            
                else:
                    # HOLD signal, no trade action taken
                    pass
            
            # Fetch updated account info after operations
            updated_balance = self.client.get_account_balance()
            updated_positions = self.client.get_positions()
            
            self.add_log("Trading loop iteration completed.")
            return {
                "balance": updated_balance,
                "positions": updated_positions,
                "logs": self.logs,
                "trades": self.trades_history
            }
            
        except Exception as e:
            self.add_log(f"CRITICAL ERROR in trading loop: {e}")
            import traceback
            self.add_log(traceback.format_exc())
            return {
                "balance": {"cash": 0.0, "net_liquidation": 0.0, "unrealized_pnl": 0.0, "currency": "USD"},
                "positions": [],
                "logs": self.logs,
                "trades": self.trades_history
            }
