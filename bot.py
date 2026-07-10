import time
import pandas as pd
from datetime import datetime, date
from config import Config
from clients.base import BaseTradingClient
from strategies.base import BaseStrategy

class TradingBot:
    """
    The main coordinator for the trading bot.
    Fetches market data, executes strategy signals, and places trades.
    Includes HK Risk Management: Stop Loss, Take Profit, Trailing Stop,
    Max Hold Days, and Daily Loss Limit.
    """

    def __init__(self, client: BaseTradingClient, strategy: BaseStrategy, symbols: list = None, market: str = "US"):
        self.client = client
        self.strategy = strategy
        self.symbols = symbols or Config.DEFAULT_SYMBOLS
        self.trade_qty_us = Config.TRADE_QUANTITY
        self.trade_qty_hk = Config.TRADE_QUANTITY_HK
        self.candle_period = Config.CANDLE_PERIOD
        self.market = market  # "US" or "HK"

        # Daily Loss Tracking (reset each calendar day)
        self._daily_loss_date: date = date.today()
        self._daily_realized_loss_hkd: float = 0.0
        self._daily_loss_limit_triggered: bool = False

        # Log lists
        self.logs = []
        self.trades_history = []

        self.add_log("Bot initialized with strategy: " + strategy.name)
        self.add_log(f"Monitoring symbols: {', '.join(self.symbols)}")
        if market == "HK":
            self.add_log(
                f"HK Risk Management -- SL: {Config.HK_STOP_LOSS_PCT}% | "
                f"TP: {Config.HK_TAKE_PROFIT_PCT}% | "
                f"Trailing: {Config.HK_TRAILING_STOP_PCT}% | "
                f"MaxHold: {Config.HK_MAX_HOLD_DAYS}d | "
                f"DailyLossLimit: {Config.HK_DAILY_LOSS_LIMIT_HKD} HKD | "
                f"ETF Qty: {Config.HK_ETF_TRADE_QTY} | "
                f"ETF SL: {Config.HK_ETF_STOP_LOSS_PCT}% | "
                f"ETF TP: {Config.HK_ETF_TAKE_PROFIT_PCT}%"
            )

    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        self.logs.append(formatted_msg)
        if len(self.logs) > 100:
            self.logs.pop(0)
        print(formatted_msg)

    def _reset_daily_loss_if_new_day(self):
        today = date.today()
        if today != self._daily_loss_date:
            self._daily_loss_date = today
            self._daily_realized_loss_hkd = 0.0
            self._daily_loss_limit_triggered = False
            self.add_log("Daily Loss counter reset for new trading day.")

    def _check_risk_exits(self, positions: list) -> list:
        exits = []
        now = datetime.now()
        trail_pct = Config.HK_TRAILING_STOP_PCT
        max_hold_days = Config.HK_MAX_HOLD_DAYS

        for pos in positions:
            symbol = pos.get("symbol", "")
            if not symbol.endswith(".HK"):
                continue
            
            # Determine if this is an ETF (usually starts with 7 or 28 in HK)
            is_etf = symbol.startswith("7") or symbol.startswith("28")
            if is_etf:
                sl_pct = Config.HK_ETF_STOP_LOSS_PCT
                tp_pct = Config.HK_ETF_TAKE_PROFIT_PCT
            else:
                sl_pct = Config.HK_STOP_LOSS_PCT
                tp_pct = Config.HK_TAKE_PROFIT_PCT
            qty = pos.get("qty", 0)
            avg_price = pos.get("avg_price", 0.0)
            if qty <= 0 or avg_price <= 0:
                continue
            market_value = pos.get("market_value", 0.0)
            current_price = market_value / qty if qty > 0 else 0.0
            if current_price <= 0:
                continue
            pnl_pct = ((current_price - avg_price) / avg_price) * 100.0
            peak_price = avg_price
            entry_time_str = ""
            try:
                portfolio_pos = self.client.portfolio.get("positions", {}).get(symbol, {})
                peak_price = portfolio_pos.get("peak_price", avg_price)
                entry_time_str = portfolio_pos.get("entry_time", "")
            except Exception:
                pass

            # 1. Stop Loss
            if sl_pct > 0 and pnl_pct <= -sl_pct:
                exits.append((symbol, qty, avg_price, current_price,
                               f"STOP LOSS triggered ({pnl_pct:.2f}% <= -{sl_pct}%)"))
                continue

            # 2. Take Profit
            if tp_pct > 0 and pnl_pct >= tp_pct:
                exits.append((symbol, qty, avg_price, current_price,
                               f"TAKE PROFIT triggered ({pnl_pct:.2f}% >= +{tp_pct}%)"))
                continue

            # 3. Trailing Stop
            if trail_pct > 0:
                if current_price > peak_price:
                    try:
                        self.client.portfolio["positions"][symbol]["peak_price"] = current_price
                        self.client._save_portfolio()
                        peak_price = current_price
                    except Exception:
                        pass
                if peak_price > 0:
                    trail_drop_pct = ((peak_price - current_price) / peak_price) * 100.0
                    if trail_drop_pct >= trail_pct:
                        exits.append((symbol, qty, avg_price, current_price,
                                      f"TRAILING STOP triggered (dropped {trail_drop_pct:.2f}% from peak {peak_price:.2f})"))
                        continue

            # 4. Max Hold Days
            if max_hold_days > 0 and entry_time_str:
                try:
                    entry_dt = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
                    hold_days = (now - entry_dt).days
                    if hold_days >= max_hold_days:
                        exits.append((symbol, qty, avg_price, current_price,
                                      f"MAX HOLD DAYS triggered (held {hold_days} days >= {max_hold_days} days)"))
                        continue
                except Exception:
                    pass

        return exits

    def _execute_risk_exit(self, symbol: str, qty, avg_price: float, current_price: float, reason: str):
        self.add_log(f"[RISK EXIT] {reason} -- Selling {qty} shares of {symbol}")
        order_res = self.client.place_order(symbol=symbol, qty=qty, action="SELL", order_type="MKT")
        if order_res.get("status") in ["FILLED", "SUBMITTED"]:
            exec_price = order_res.get("price", current_price)
            realized_pnl = (exec_price - avg_price) * qty
            self.add_log(f"[RISK EXIT] Sold {qty} shares of {symbol} at {exec_price:.2f} HKD | PnL: {realized_pnl:+.2f} HKD")
            self.trades_history.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "symbol": symbol,
                "action": "SELL (RISK)",
                "qty": qty,
                "price": exec_price,
                "status": order_res.get("status"),
                "reason": reason
            })
            if realized_pnl < 0:
                self._daily_realized_loss_hkd += abs(realized_pnl)
        else:
            self.add_log(f"[RISK EXIT] FAILED to place SELL for {symbol}: {order_res.get('reason', 'Unknown')}")

    def run_once(self) -> dict:
        self.add_log("Starting trading loop iteration...")
        try:
            self._reset_daily_loss_if_new_day()
            balance = self.client.get_account_balance()
            positions = self.client.get_positions()
            pos_map = {pos["symbol"]: pos for pos in positions}

            # HK Risk Management
            if self.market == "HK":
                daily_limit = Config.HK_DAILY_LOSS_LIMIT_HKD
                if daily_limit > 0 and self._daily_realized_loss_hkd >= daily_limit:
                    if not self._daily_loss_limit_triggered:
                        self._daily_loss_limit_triggered = True
                        self.add_log(
                            f"[RISK] DAILY LOSS LIMIT reached: "
                            f"{self._daily_realized_loss_hkd:.2f} HKD >= {daily_limit:.2f} HKD -- "
                            f"HK Bot paused for today."
                        )
                    self.add_log("HK Bot is paused due to Daily Loss Limit. Skipping this iteration.")
                    updated_balance = self.client.get_account_balance()
                    updated_positions = self.client.get_positions()
                    return {"balance": updated_balance, "positions": updated_positions, "logs": self.logs, "trades": self.trades_history}

                hk_exits = self._check_risk_exits(positions)
                for symbol, qty, avg_price, current_price, reason in hk_exits:
                    self._execute_risk_exit(symbol, qty, avg_price, current_price, reason)
                positions = self.client.get_positions()
                pos_map = {pos["symbol"]: pos for pos in positions}

            for symbol in self.symbols:
                self.add_log(f"Analyzing {symbol}...")
                df = self.client.get_bars(symbol=symbol, interval=self.candle_period, limit=100)
                if df.empty:
                    self.add_log(f"Warning: No historical data received for {symbol}. Skipping.")
                    continue
                current_price = float(df["close"].iloc[-1])
                self.add_log(f"Current price for {symbol}: ${current_price:.2f}")
                signal = self.strategy.generate_signal(df)
                self.add_log(f"Strategy signal for {symbol}: {signal}")
                owned_position = pos_map.get(symbol)
                owned_qty = owned_position["qty"] if owned_position else 0

                if signal == "BUY":
                    if symbol.endswith(".HK"):
                        slot_size = min(self.trade_qty_hk, Config.HK_MAX_QTY_PER_SLOT)
                        current_slots = int(owned_qty / slot_size) if slot_size > 0 else 0
                        if current_slots >= Config.HK_MAX_SLOTS:
                            self.add_log(f"Signal is BUY for {symbol} but already own {owned_qty} shares ({current_slots}/{Config.HK_MAX_SLOTS} slots). Skipping.")
                        elif current_price > Config.HK_FILTER_PRICE_LIMIT:
                            self.add_log(f"Signal is BUY for {symbol} but current price ${current_price:.2f} is above target filter price limit ${Config.HK_FILTER_PRICE_LIMIT:.2f}. Skipping.")
                        else:
                            qty_to_trade = slot_size
                            if qty_to_trade <= 0:
                                self.add_log(f"Signal is BUY for {symbol} but slot quantity size is {qty_to_trade}. Skipping.")
                            else:
                                self.add_log(f"Signal: BUY {qty_to_trade} shares of {symbol} (Slot {current_slots + 1}/{Config.HK_MAX_SLOTS})...")
                                order_res = self.client.place_order(symbol=symbol, qty=qty_to_trade, action="BUY", order_type="MKT")
                                if order_res.get("status") in ["FILLED", "SUBMITTED"]:
                                    exec_price = order_res.get("price", current_price)
                                    self.add_log(f"SUCCESS: Bought {qty_to_trade} shares of {symbol} at ${exec_price:.2f} (Slot {current_slots + 1}/{Config.HK_MAX_SLOTS})")
                                    self.trades_history.append({"time": datetime.now().strftime("%H:%M:%S"), "symbol": symbol, "action": "BUY", "qty": qty_to_trade, "price": exec_price, "status": order_res.get("status")})
                                else:
                                    self.add_log(f"FAILED to place BUY order for {symbol}: {order_res.get('reason', 'Unknown reason')}")
                    else:
                        if owned_qty > 0:
                            self.add_log(f"Signal is BUY but already own {owned_qty} shares of {symbol}. Skipping.")
                        else:
                            qty_to_trade = round(float(self.trade_qty_us) / current_price, 4) if current_price > 0 else 0
                            if qty_to_trade <= 0:
                                self.add_log(f"Signal is BUY for {symbol} but calculated trade quantity is {qty_to_trade}. Skipping.")
                            else:
                                self.add_log(f"Signal: BUY {qty_to_trade} shares of {symbol} (Budget: ${self.trade_qty_us})...")
                                order_res = self.client.place_order(symbol=symbol, qty=qty_to_trade, action="BUY", order_type="MKT")
                                if order_res.get("status") in ["FILLED", "SUBMITTED"]:
                                    exec_price = order_res.get("price", current_price)
                                    self.add_log(f"SUCCESS: Bought {qty_to_trade} shares of {symbol} at ${exec_price:.2f}")
                                    self.trades_history.append({"time": datetime.now().strftime("%H:%M:%S"), "symbol": symbol, "action": "BUY", "qty": qty_to_trade, "price": exec_price, "status": order_res.get("status")})
                                else:
                                    self.add_log(f"FAILED to place BUY order for {symbol}: {order_res.get('reason', 'Unknown reason')}")

                elif signal == "SELL":
                    if owned_qty <= 0:
                        self.add_log(f"Signal is SELL but do not own any shares of {symbol}. Skipping.")
                    else:
                        self.add_log(f"Signal: SELL {owned_qty} shares of {symbol}...")
                        order_res = self.client.place_order(symbol=symbol, qty=owned_qty, action="SELL", order_type="MKT")
                        if order_res.get("status") in ["FILLED", "SUBMITTED"]:
                            exec_price = order_res.get("price", current_price)
                            self.add_log(f"SUCCESS: Sold {owned_qty} shares of {symbol} at ${exec_price:.2f}")
                            self.trades_history.append({"time": datetime.now().strftime("%H:%M:%S"), "symbol": symbol, "action": "SELL", "qty": owned_qty, "price": exec_price, "status": order_res.get("status")})
                        else:
                            self.add_log(f"FAILED to place SELL order for {symbol}: {order_res.get('reason', 'Unknown reason')}")

            updated_balance = self.client.get_account_balance()
            updated_positions = self.client.get_positions()
            self.add_log("Trading loop iteration completed.")
            return {"balance": updated_balance, "positions": updated_positions, "logs": self.logs, "trades": self.trades_history}

        except Exception as e:
            self.add_log(f"CRITICAL ERROR in trading loop: {e}")
            import traceback
            self.add_log(traceback.format_exc())
            return {"balance": {"cash": 0.0, "net_liquidation": 0.0, "unrealized_pnl": 0.0, "currency": "USD"}, "positions": [], "logs": self.logs, "trades": self.trades_history}
