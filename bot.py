import time
import pandas as pd
from datetime import datetime, date, time as dt_time
from zoneinfo import ZoneInfo
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
        self._daily_realized_loss_usd: float = 0.0
        self._recent_submitted: dict = {}
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
            self._daily_realized_loss_usd = 0.0
            self._daily_loss_limit_triggered = False
            self.add_log("Daily Loss counter reset for new trading day.")

    def _is_market_open(self) -> bool:
        if not Config.REGULAR_HOURS_ONLY:
            return True
        if self.market == "HK":
            return True  # Existing HK execution rules are broker-specific.
        now = datetime.now(ZoneInfo("America/New_York"))
        if now.weekday() >= 5:
            return False
        return dt_time(9, 30) <= now.time() < dt_time(16, 0)

    def _is_inverse_etf(self, symbol: str) -> bool:
        return symbol in set(Config.INVERSE_ETF_MAP.values())

    def _closed_bars(self, df: pd.DataFrame) -> pd.DataFrame:
        """Use only completed intraday bars to prevent signals from repainting."""
        if self.candle_period != "d" and len(df) > 3:
            return df.iloc[:-1].copy()
        return df

    def _order_is_working(self, symbol: str, working_symbols: set) -> bool:
        return symbol.upper() in {str(item).upper() for item in working_symbols}
    def _check_risk_exits(self, positions: list) -> list:
        exits = []
        now = datetime.now()
        for pos in positions:
            symbol = pos.get("symbol", "")
            is_hk = symbol.endswith(".HK")
            if self.market == "US" and is_hk:
                continue
            if self.market == "HK" and not is_hk:
                continue
            is_etf = self._is_inverse_etf(symbol) if self.market == "US" else (symbol.startswith("7") or symbol.startswith("28"))
            if self.market == "US":
                sl_pct = Config.US_ETF_STOP_LOSS_PCT if is_etf else Config.US_STOP_LOSS_PCT
                tp_pct = Config.US_ETF_TAKE_PROFIT_PCT if is_etf else Config.US_TAKE_PROFIT_PCT
                trail_pct = Config.US_ETF_TRAILING_STOP_PCT if is_etf else Config.US_TRAILING_STOP_PCT
                max_hold_days = Config.US_MAX_HOLD_DAYS
            else:
                sl_pct = Config.HK_ETF_STOP_LOSS_PCT if is_etf else Config.HK_STOP_LOSS_PCT
                tp_pct = Config.HK_ETF_TAKE_PROFIT_PCT if is_etf else Config.HK_TAKE_PROFIT_PCT
                trail_pct = Config.HK_TRAILING_STOP_PCT
                max_hold_days = Config.HK_MAX_HOLD_DAYS
            qty = float(pos.get("qty", 0))
            avg_price = float(pos.get("avg_price", 0.0))
            if qty <= 0 or avg_price <= 0:
                continue
            current_price = float(pos.get("market_value", 0.0)) / qty
            if current_price <= 0:
                continue
            pnl_pct = ((current_price - avg_price) / avg_price) * 100.0
            portfolio_pos = getattr(self.client, "portfolio", {}).get("positions", {}).get(symbol, {})
            peak_price = float(portfolio_pos.get("peak_price", avg_price))
            entry_time_str = portfolio_pos.get("entry_time", "")
            if sl_pct > 0 and pnl_pct <= -sl_pct:
                exits.append((symbol, qty, avg_price, current_price, f"STOP LOSS triggered ({pnl_pct:.2f}% <= -{sl_pct}%)")); continue
            if tp_pct > 0 and pnl_pct >= tp_pct:
                exits.append((symbol, qty, avg_price, current_price, f"TAKE PROFIT triggered ({pnl_pct:.2f}% >= +{tp_pct}%)")); continue
            if trail_pct > 0:
                if current_price > peak_price:
                    try:
                        self.client.portfolio["positions"][symbol]["peak_price"] = current_price
                        self.client._save_portfolio()
                        peak_price = current_price
                    except Exception:
                        pass
                if peak_price > 0 and ((peak_price - current_price) / peak_price) * 100.0 >= trail_pct:
                    exits.append((symbol, qty, avg_price, current_price, f"TRAILING STOP triggered (dropped {((peak_price-current_price)/peak_price)*100.0:.2f}%)")); continue
            if max_hold_days > 0 and entry_time_str:
                try:
                    hold_days = (now - datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")).days
                    if hold_days >= max_hold_days:
                        exits.append((symbol, qty, avg_price, current_price, f"MAX HOLD DAYS triggered ({hold_days} >= {max_hold_days})"))
                except (TypeError, ValueError):
                    pass
        return exits
    def _execute_risk_exit(self, symbol: str, qty, avg_price: float, current_price: float, reason: str):
        self.add_log(f"[RISK EXIT] {reason} -- Selling {qty} shares of {symbol}")
        order_res = self.client.place_order(symbol=symbol, qty=qty, action="SELL", order_type="MKT")
        if order_res.get("status") in ["FILLED", "SUBMITTED"]:
            exec_price = order_res.get("price", current_price)
            realized_pnl = (exec_price - avg_price) * qty
            currency = "HKD" if self.market == "HK" else "USD"
            self.add_log(f"[RISK EXIT] Exit order {order_res.get('status')} for {qty} shares of {symbol} at {exec_price:.2f} {currency} | estimated PnL: {realized_pnl:+.2f} {currency}")
            self.trades_history.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "symbol": symbol,
                "action": "SELL (RISK)",
                "qty": qty,
                "price": exec_price,
                "status": order_res.get("status"),
                "reason": reason
            })
            if order_res.get("status") == "FILLED" and realized_pnl < 0:
                if self.market == "US":
                    self._daily_realized_loss_usd += abs(realized_pnl)
                else:
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

            daily_limit = Config.HK_DAILY_LOSS_LIMIT_HKD if self.market == "HK" else Config.US_DAILY_LOSS_LIMIT_USD
            daily_loss = self._daily_realized_loss_hkd if self.market == "HK" else self._daily_realized_loss_usd
            if daily_limit > 0 and daily_loss >= daily_limit:
                self.add_log(f"[RISK] DAILY LOSS LIMIT reached: {daily_loss:.2f} >= {daily_limit:.2f}. Bot paused.")
                return {"balance": balance, "positions": positions, "logs": self.logs, "trades": self.trades_history}

            if not self._is_market_open():
                self.add_log(f"{self.market} market is closed; skipping orders.")
                return {"balance": balance, "positions": positions, "logs": self.logs, "trades": self.trades_history}

            risk_exits = self._check_risk_exits(positions)
            for symbol, qty, avg_price, current_price, reason in risk_exits:
                self._execute_risk_exit(symbol, qty, avg_price, current_price, reason)
            positions = self.client.get_positions()
            pos_map = {pos["symbol"]: pos for pos in positions}
            try:
                working_symbols = {o.get("symbol") for o in self.client.get_working_orders() if o.get("symbol")}
            except Exception:
                working_symbols = set()
            for symbol in self.symbols:
                if self._order_is_working(symbol, working_symbols):
                    self.add_log(f'Skipping {symbol}: working order already exists.')
                    continue
                self.add_log(f"Analyzing {symbol}...")
                df = self.client.get_bars(symbol=symbol, interval=self.candle_period, limit=100)
                df = self._closed_bars(df)
                if df.empty:
                    self.add_log(f"Warning: No historical data received for {symbol}. Skipping.")
                    continue
                current_price = float(df["close"].iloc[-1])
                self.add_log(f"Current price for {symbol}: ${current_price:.2f}")
                signal = self.strategy.generate_signal(df)
                self.add_log(f"Strategy signal for {symbol}: {signal}")
                owned_position = pos_map.get(symbol)
                owned_qty = owned_position["qty"] if owned_position else 0

                # --- Automated ETF Hedging Block ---
                is_hk = symbol.endswith(".HK")
                enable_hedging = Config.ENABLE_INVERSE_ETF_HEDGING if is_hk else Config.US_ENABLE_INVERSE_ETF_HEDGING
                
                if enable_hedging:
                    etf_symbol = Config.INVERSE_ETF_MAP.get(symbol)
                    if etf_symbol:
                        self.add_log(f"Evaluating ETF Hedging for {symbol} with ETF {etf_symbol}...")
                        from strategies import get_strategy
                        etf_strat_name = Config.HK_ETF_STRATEGY if is_hk else Config.US_ETF_STRATEGY
                        etf_signal = "HOLD"
                        try:
                            if etf_strat_name == "all":
                                sma_strat = get_strategy("sma")
                                rsi_strat = get_strategy("rsi")
                                hybrid_strat = get_strategy("hybrid")
                                sma_sig = sma_strat.generate_signal(df)
                                rsi_sig = rsi_strat.generate_signal(df)
                                hyb_sig = hybrid_strat.generate_signal(df)
                                
                                sma_score = 1 if sma_sig == "SELL" else (-1 if sma_sig == "BUY" else 0)
                                rsi_score = 1 if rsi_sig == "SELL" else (-1 if rsi_sig == "BUY" else 0)
                                hyb_score = 1 if hyb_sig == "SELL" else (-1 if hyb_sig == "BUY" else 0)
                                score = sma_score + rsi_score + hyb_score
                                if score >= 2:
                                    etf_signal = "BUY"
                                elif score <= -2:
                                    etf_signal = "SELL"
                            else:
                                if etf_strat_name in ["volume_ema", "sma", "rsi", "hybrid", "regime_adaptive", "short_regime"]:
                                    strat = get_strategy(etf_strat_name)
                                else:
                                    strat = self.strategy
                                stock_sig = strat.generate_signal(df)
                                if stock_sig == "SELL":
                                    etf_signal = "BUY"
                                elif stock_sig == "BUY":
                                    etf_signal = "SELL"
                            
                            self.add_log(f"ETF signal for {etf_symbol} based on {symbol}: {etf_signal}")
                            owned_etf_qty = pos_map.get(etf_symbol, {}).get("qty", 0)
                            
                            if etf_signal == "BUY":
                                if (not is_hk and not Config.US_ALLOW_NAKED_INVERSE and owned_qty <= 0):
                                    self.add_log(f"Skipping inverse ETF BUY for {etf_symbol}: no underlying Long position to hedge.")
                                    continue
                                if self._order_is_working(etf_symbol, working_symbols):
                                    self.add_log(f"Skipping ETF BUY for {etf_symbol}: working order already exists.")
                                    continue
                                if is_hk:
                                    slot_size = Config.HK_ETF_TRADE_QTY
                                    current_etf_slots = int(owned_etf_qty / slot_size) if slot_size > 0 else 0
                                    if current_etf_slots >= Config.HK_MAX_SLOTS:
                                        self.add_log(f"Auto-Hedge is BUY for {etf_symbol} but already own max ETF slots ({current_etf_slots}/{Config.HK_MAX_SLOTS}). Skipping.")
                                    else:
                                        self.add_log(f"Auto-Hedge Signal: BUY {slot_size} shares of ETF {etf_symbol}...")
                                        order_res = self.client.place_order(symbol=etf_symbol, qty=slot_size, action="BUY", order_type="MKT")
                                        if order_res.get("status") in ["FILLED", "SUBMITTED"]:
                                            exec_price = order_res.get("price", 0.0)
                                            self.add_log(f"SUCCESS: Auto-Hedge Bought {slot_size} shares of ETF {etf_symbol} at ${exec_price:.2f}")
                                            self.trades_history.append({"time": datetime.now().strftime("%H:%M:%S"), "symbol": etf_symbol, "action": "BUY (HEDGE)", "qty": slot_size, "price": exec_price, "status": order_res.get("status")})
                                        else:
                                            self.add_log(f"FAILED to place Auto-Hedge BUY order for {etf_symbol}: {order_res.get('reason', 'Unknown reason')}")
                                else:
                                    # US ETF Hedging BUY
                                    if owned_etf_qty > 0:
                                        self.add_log(f"Auto-Hedge is BUY for US ETF {etf_symbol} but already own {owned_etf_qty} shares. Skipping.")
                                    else:
                                        etf_curr_price = current_price
                                        try:
                                            etf_df = self.client.get_bars(symbol=etf_symbol, interval=self.candle_period, limit=1)
                                            if not etf_df.empty:
                                                etf_curr_price = float(etf_df["close"].iloc[-1])
                                        except Exception:
                                            pass
                                        
                                        hedge_budget = min(float(Config.US_ETF_BUDGET), max(0.0, float(owned_qty) * current_price * float(Config.US_HEDGE_RATIO)))
                                        slot_size = round(hedge_budget / etf_curr_price, 4) if etf_curr_price > 0 else 0
                                        if slot_size <= 0:
                                            self.add_log(f"Auto-Hedge is BUY for US ETF {etf_symbol} but calculated quantity is {slot_size}. Skipping.")
                                        else:
                                            self.add_log(f"Auto-Hedge Signal: BUY {slot_size} shares of US ETF {etf_symbol} (Budget: ${hedge_budget:.2f})...")
                                            order_res = self.client.place_order(symbol=etf_symbol, qty=slot_size, action="BUY", order_type="MKT")
                                            if order_res.get("status") in ["FILLED", "SUBMITTED"]:
                                                exec_price = order_res.get("price", etf_curr_price)
                                                self.add_log(f"SUCCESS: Auto-Hedge Bought {slot_size} shares of ETF {etf_symbol} at ${exec_price:.2f}")
                                                self.trades_history.append({"time": datetime.now().strftime("%H:%M:%S"), "symbol": etf_symbol, "action": "BUY (HEDGE)", "qty": slot_size, "price": exec_price, "status": order_res.get("status")})
                                            else:
                                                self.add_log(f"FAILED to place Auto-Hedge BUY order for {etf_symbol}: {order_res.get('reason', 'Unknown reason')}")
                            
                            elif etf_signal == "SELL":
                                if self._order_is_working(etf_symbol, working_symbols):
                                    self.add_log(f"Skipping ETF SELL for {etf_symbol}: working order already exists.")
                                    continue
                                if owned_etf_qty <= 0:
                                    self.add_log(f"Auto-Hedge is SELL but do not own any shares of ETF {etf_symbol}. Skipping.")
                                else:
                                    self.add_log(f"Auto-Hedge Signal: SELL {owned_etf_qty} shares of ETF {etf_symbol} to close hedge...")
                                    order_res = self.client.place_order(symbol=etf_symbol, qty=owned_etf_qty, action="SELL", order_type="MKT")
                                    if order_res.get("status") in ["FILLED", "SUBMITTED"]:
                                        exec_price = order_res.get("price", 0.0)
                                        self.add_log(f"SUCCESS: Auto-Hedge Sold {owned_etf_qty} shares of ETF {etf_symbol} at ${exec_price:.2f}")
                                        self.trades_history.append({"time": datetime.now().strftime("%H:%M:%S"), "symbol": etf_symbol, "action": "SELL (HEDGE)", "qty": owned_etf_qty, "price": exec_price, "status": order_res.get("status")})
                                    else:
                                        self.add_log(f"FAILED to place Auto-Hedge SELL order for {etf_symbol}: {order_res.get('reason', 'Unknown reason')}")
                        except Exception as ex:
                            self.add_log(f"Error executing ETF Hedge logic: {ex}")
                # --- End ETF Hedging Block ---

                if signal == "BUY":
                    if is_hk:
                        if not Config.HK_AUTO_LONG:
                            self.add_log(f"Signal is BUY for HK stock {symbol} but HK Auto-Long is disabled. Skipping stock order.")
                        else:
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
                        if not Config.US_AUTO_LONG:
                            self.add_log(f"Signal is BUY for US stock {symbol} but US Auto-Long is disabled. Skipping stock order.")
                        else:
                            if owned_qty > 0:
                                self.add_log(f"Signal is BUY but already own {owned_qty} shares of {symbol}. Skipping.")
                            else:
                                if float(self.trade_qty_us) < Config.US_MIN_ORDER_VALUE:
                                    self.add_log(f"Signal is BUY for {symbol} but budget ${self.trade_qty_us:.2f} is below minimum ${Config.US_MIN_ORDER_VALUE:.2f}. Skipping.")
                                    continue
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
                        if is_hk and not Config.HK_AUTO_LONG:
                            self.add_log(f"Signal is SELL for HK stock {symbol} but HK Auto-Long is disabled. Skipping stock order.")
                        elif not is_hk and not Config.US_AUTO_LONG:
                            self.add_log(f"Signal is SELL for US stock {symbol} but US Auto-Long is disabled. Skipping stock order.")
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
