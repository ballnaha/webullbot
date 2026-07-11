import os
import asyncio
import importlib
import threading
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from config import Config
from clients import get_client
from strategies import get_strategy
from bot import TradingBot

app = FastAPI(title="Webull Trading Bot API", version="1.0.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot state storage
bot_state = {
    "running_us": False,
    "running_hk": False,
    "bot_us": None,
    "bot_hk": None,
    "client": None,
    "strategy_us": "sma",
    "strategy_hk": "rsi",
    "init_status": "idle",
    "init_error": "",
    "latest_data": {
        "balance": {
            "cash": 0.0, "net_liquidation": 0.0, "unrealized_pnl": 0.0, "currency": "USD",
            "cash_hkd": 0.0, "net_liquidation_hkd": 0.0, "unrealized_pnl_hkd": 0.0, "currency_hkd": "HKD"
        },
        "positions": [],
        "logs": ["Server started. Bot is idle."],
        "trades": []
    }
}

# Lock for config updates
config_lock = threading.Lock()

def add_system_log(message: str):
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] [SYSTEM] {message}"
    bot_state["latest_data"]["logs"].append(formatted_msg)
    if len(bot_state["latest_data"]["logs"]) > 100:
        bot_state["latest_data"]["logs"].pop(0)
    print(formatted_msg)

def _bg_init_components():
    bot_state["init_status"] = "initializing"
    bot_state["init_error"] = ""
    try:
        # Validate config first
        ok, msg = Config.validate()
        if not ok:
            bot_state["init_status"] = "failed"
            bot_state["init_error"] = msg
            add_system_log(f"Configuration validation failed: {msg}")
            return

        add_system_log(f"Initializing trading client for mode: {Config.TRADE_MODE}...")
        client = get_client()
        
        # Attempt login
        login_ok = client.login()
        if not login_ok:
            bot_state["init_status"] = "failed"
            bot_state["init_error"] = "Failed to login to Webull. Check credentials in settings."
            add_system_log("Failed to login to Webull. Check credentials in settings.")
            return
            
        bot_state["client"] = client
        
        # Load strategies
        bot_state["strategy_us"] = Config.STRATEGY_US
        bot_state["strategy_hk"] = Config.STRATEGY_HK
        
        # Load US strategy
        add_system_log(f"Loading US strategy: {Config.STRATEGY_US}...")
        if Config.STRATEGY_US == "sma":
            strategy_us = get_strategy("sma", fast_period=10, slow_period=30)
        elif Config.STRATEGY_US == "hybrid":
            strategy_us = get_strategy("hybrid", fast_period=10, slow_period=30, period=14, oversold=40.0, overbought=60.0)
        elif Config.STRATEGY_US == "volume_ema":
            strategy_us = get_strategy("volume_ema", fast_period=9, slow_period=21, vol_period=20, vol_factor=2.5)
        elif Config.STRATEGY_US == "regime_adaptive":
            strategy_us = get_strategy("regime_adaptive", fast_period=20, slow_period=50, rsi_period=14, rsi_entry=45.0, rsi_exit=40.0, rsi_ceiling=68.0)
        else:
            strategy_us = get_strategy("rsi", period=14, oversold=30.0, overbought=70.0)
            
        # Load HK strategy
        add_system_log(f"Loading HK strategy: {Config.STRATEGY_HK}...")
        if Config.STRATEGY_HK == "sma":
            strategy_hk = get_strategy(
                "sma",
                fast_period=Config.HK_SMA_FAST_PERIOD,
                slow_period=Config.HK_SMA_SLOW_PERIOD,
            )
        elif Config.STRATEGY_HK == "hybrid":
            strategy_hk = get_strategy("hybrid", fast_period=10, slow_period=30, period=14, oversold=40.0, overbought=60.0)
        elif Config.STRATEGY_HK == "volume_ema":
            strategy_hk = get_strategy("volume_ema", fast_period=9, slow_period=21, vol_period=20, vol_factor=2.5)
        elif Config.STRATEGY_HK == "regime_adaptive":
            strategy_hk = get_strategy("regime_adaptive", fast_period=20, slow_period=50, rsi_period=14, rsi_entry=45.0, rsi_exit=40.0, rsi_ceiling=68.0)
        else:
            strategy_hk = get_strategy("rsi", period=14, oversold=30.0, overbought=70.0)
            
        # Split symbols
        us_symbols = [s for s in Config.DEFAULT_SYMBOLS if not s.endswith(".HK")]
        hk_symbols = [s for s in Config.DEFAULT_SYMBOLS if s.endswith(".HK")]
            
        # Create bot orchestrators
        bot_state["bot_us"] = TradingBot(client=client, strategy=strategy_us, symbols=us_symbols, market="US")
        bot_state["bot_hk"] = TradingBot(client=client, strategy=strategy_hk, symbols=hk_symbols, market="HK")
        add_system_log("Bot components successfully initialized for both US and HK markets!")
        
        # Initial data fetch
        balance = client.get_account_balance()
        positions = client.get_positions()
        bot_state["latest_data"]["balance"] = balance
        bot_state["latest_data"]["positions"] = positions
        
        # Load transactions from client portfolio if local paper trading
        if hasattr(client, "portfolio") and "transactions" in client.portfolio:
            bot_state["latest_data"]["trades"] = client.portfolio["transactions"]
        
        bot_state["init_status"] = "success"
        bot_state["init_error"] = ""
    except Exception as e:
        error_msg = f"Initialization error: {e}"
        add_system_log(error_msg)
        bot_state["init_status"] = "failed"
        bot_state["init_error"] = error_msg

def init_bot_components():
    """
    Initializes bot components asynchronously in a background thread.
    """
    t = threading.Thread(target=_bg_init_components, name="BotInitThread")
    t.daemon = True
    t.start()
    return True, "Reinitialization started in the background"

# Background task for bot trading execution
async def trading_loop():
    add_system_log("Background trading loop task started.")
    while True:
        # 1. Run US Bot if enabled
        if bot_state["running_us"]:
            if bot_state["bot_us"]:
                try:
                    add_system_log("Executing background US bot trade scan...")
                    res = bot_state["bot_us"].run_once()
                    bot_state["latest_data"]["balance"] = res["balance"]
                    bot_state["latest_data"]["positions"] = res["positions"]
                    
                    # Merge logs
                    for log in res["logs"]:
                        if log not in bot_state["latest_data"]["logs"]:
                            bot_state["latest_data"]["logs"].append(log)
                    
                    # Keep logs capped
                    if len(bot_state["latest_data"]["logs"]) > 100:
                        bot_state["latest_data"]["logs"] = bot_state["latest_data"]["logs"][-100:]
                        
                    # Add new trades to history
                    for trade in res.get("trades", []):
                        if trade not in bot_state["latest_data"]["trades"]:
                            bot_state["latest_data"]["trades"].append(trade)
                except Exception as e:
                    add_system_log(f"Error in US trading loop: {e}")
            else:
                add_system_log("Warning: US Bot is active but bot_us instance is None. Attempting reinitialization...")
                success, _ = init_bot_components()
                if not success:
                    add_system_log("Reinitialization failed. Stopping US bot.")
                    bot_state["running_us"] = False
                    
        # 2. Run HK Bot if enabled
        if bot_state["running_hk"]:
            if bot_state["bot_hk"]:
                try:
                    add_system_log("Executing background HK bot trade scan...")
                    res = bot_state["bot_hk"].run_once()
                    bot_state["latest_data"]["balance"] = res["balance"]
                    bot_state["latest_data"]["positions"] = res["positions"]
                    
                    # Merge logs
                    for log in res["logs"]:
                        if log not in bot_state["latest_data"]["logs"]:
                            bot_state["latest_data"]["logs"].append(log)
                    
                    # Keep logs capped
                    if len(bot_state["latest_data"]["logs"]) > 100:
                        bot_state["latest_data"]["logs"] = bot_state["latest_data"]["logs"][-100:]
                        
                    # Add new trades to history
                    for trade in res.get("trades", []):
                        if trade not in bot_state["latest_data"]["trades"]:
                            bot_state["latest_data"]["trades"].append(trade)
                except Exception as e:
                    add_system_log(f"Error in HK trading loop: {e}")
            else:
                add_system_log("Warning: HK Bot is active but bot_hk instance is None. Attempting reinitialization...")
                success, _ = init_bot_components()
                if not success:
                    add_system_log("Reinitialization failed. Stopping HK bot.")
                    bot_state["running_hk"] = False

        if bot_state["running_us"] or bot_state["running_hk"]:
            await asyncio.sleep(Config.INTERVAL)
        else:
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    # Initialize bot on startup
    init_bot_components()
    # Launch background loop
    asyncio.create_task(trading_loop())

class ConfigModel(BaseModel):
    trade_mode: str
    symbols: List[str]
    quantity: float
    quantity_hk: Optional[int] = 100
    hk_max_slots: Optional[int] = None
    hk_max_price_per_slot: Optional[float] = None
    hk_max_qty_per_slot: Optional[int] = None
    hk_filter_price_limit: Optional[float] = 20.0
    hk_filter_price_operator: Optional[str] = "le"
    strategy_us: Optional[str] = None
    strategy_hk: Optional[str] = None
    strategy: Optional[str] = "sma"
    interval: int
    candle_period: str
    # Credentials optional updates
    username: Optional[str] = ""
    password: Optional[str] = ""
    trade_pin: Optional[str] = ""
    app_key: Optional[str] = ""
    app_secret: Optional[str] = ""
    webull_api_endpoint: Optional[str] = ""
    webull_api_region: Optional[str] = None
    simulated_initial_cash: Optional[float] = None
    simulated_initial_cash_hkd: Optional[float] = None
    # HK Risk Management
    hk_stop_loss_pct: Optional[float] = None
    hk_take_profit_pct: Optional[float] = None
    hk_trailing_stop_pct: Optional[float] = None
    hk_max_hold_days: Optional[int] = None
    hk_daily_loss_limit_hkd: Optional[float] = None
    # HK ETF Settings
    hk_etf_trade_qty: Optional[int] = 100
    hk_etf_stop_loss_pct: Optional[float] = 8.0
    hk_etf_take_profit_pct: Optional[float] = 15.0
    hk_etf_strategy: Optional[str] = "trend_cash_3067"
    hk_auto_long: Optional[bool] = True
    enable_inverse_etf_hedging: Optional[bool] = False
    
    # US ETF Settings
    us_auto_long: Optional[bool] = True
    us_enable_inverse_etf_hedging: Optional[bool] = True
    us_etf_budget: Optional[float] = 300.0
    us_etf_strategy: Optional[str] = "standard"
    us_stop_loss_pct: Optional[float] = None
    us_take_profit_pct: Optional[float] = None
    us_trailing_stop_pct: Optional[float] = None
    us_max_hold_days: Optional[int] = None
    us_daily_loss_limit_usd: Optional[float] = None
    us_etf_stop_loss_pct: Optional[float] = None
    us_etf_take_profit_pct: Optional[float] = None
    us_etf_trailing_stop_pct: Optional[float] = None

class OrderModel(BaseModel):
    symbol: str
    qty: float
    action: str  # BUY or SELL
    order_type: str = "MKT"  # MKT or LMT
    price: Optional[float] = None

@app.get("/api/status")
def get_status():
    return {
        "running": bot_state["running_us"] or bot_state["running_hk"],
        "running_us": bot_state["running_us"],
        "running_hk": bot_state["running_hk"],
        "trade_mode": Config.TRADE_MODE,
        "strategy": bot_state["strategy_us"],
        "strategy_us": Config.STRATEGY_US,
        "strategy_hk": Config.STRATEGY_HK,
        "symbols": Config.DEFAULT_SYMBOLS,
        "quantity": Config.TRADE_QUANTITY,
        "quantity_hk": Config.TRADE_QUANTITY_HK,
        "hk_trade_budget_hkd": Config.HK_TRADE_BUDGET_HKD,
        "hk_etf_budget_hkd": Config.HK_ETF_BUDGET_HKD,
        "hk_max_slots": Config.HK_MAX_SLOTS,
        "hk_max_price_per_slot": Config.HK_MAX_PRICE_PER_SLOT,
        "hk_max_qty_per_slot": Config.HK_MAX_QTY_PER_SLOT,
        "hk_filter_price_limit": Config.HK_FILTER_PRICE_LIMIT,
        "hk_filter_price_operator": Config.HK_FILTER_PRICE_OPERATOR,
        "interval": Config.INTERVAL,
        "candle_period": Config.CANDLE_PERIOD,
        "simulated_initial_cash": Config.SIMULATED_INITIAL_CASH,
        "simulated_initial_cash_hkd": Config.SIMULATED_INITIAL_CASH_HKD,
        "has_client": bot_state["client"] is not None,
        "init_status": bot_state.get("init_status", "idle"),
        "init_error": bot_state.get("init_error", ""),
        # HK Risk Management
        "hk_stop_loss_pct": Config.HK_STOP_LOSS_PCT,
        "hk_take_profit_pct": Config.HK_TAKE_PROFIT_PCT,
        "hk_trailing_stop_pct": Config.HK_TRAILING_STOP_PCT,
        "hk_max_hold_days": Config.HK_MAX_HOLD_DAYS,
        "hk_daily_loss_limit_hkd": Config.HK_DAILY_LOSS_LIMIT_HKD,
        # HK ETF Settings
        "hk_etf_trade_qty": Config.HK_ETF_TRADE_QTY,
        "hk_etf_stop_loss_pct": Config.HK_ETF_STOP_LOSS_PCT,
        "hk_etf_take_profit_pct": Config.HK_ETF_TAKE_PROFIT_PCT,
        "hk_etf_strategy": Config.HK_ETF_STRATEGY,
        "hk_auto_long": Config.HK_AUTO_LONG,
        "enable_inverse_etf_hedging": Config.ENABLE_INVERSE_ETF_HEDGING,
        "us_auto_long": Config.US_AUTO_LONG,
        "us_enable_inverse_etf_hedging": Config.US_ENABLE_INVERSE_ETF_HEDGING,
        "us_etf_budget": Config.US_ETF_BUDGET,
        "us_etf_strategy": Config.US_ETF_STRATEGY,
        "us_allow_naked_inverse": Config.US_ALLOW_NAKED_INVERSE,
        "us_hedge_ratio": Config.US_HEDGE_RATIO,
        "us_stop_loss_pct": Config.US_STOP_LOSS_PCT,
        "us_take_profit_pct": Config.US_TAKE_PROFIT_PCT,
        "us_trailing_stop_pct": Config.US_TRAILING_STOP_PCT,
        "us_max_hold_days": Config.US_MAX_HOLD_DAYS,
        "us_daily_loss_limit_usd": Config.US_DAILY_LOSS_LIMIT_USD,
        "us_etf_stop_loss_pct": Config.US_ETF_STOP_LOSS_PCT,
        "us_etf_take_profit_pct": Config.US_ETF_TAKE_PROFIT_PCT,
        "us_etf_trailing_stop_pct": Config.US_ETF_TRAILING_STOP_PCT,
    }

@app.get("/api/portfolio")
def get_portfolio():
    # Attempt to fetch fresh data if client is connected, otherwise return cached data
    if bot_state["client"]:
        try:
            balance = bot_state["client"].get_account_balance()
            positions = bot_state["client"].get_positions()
            bot_state["latest_data"]["balance"] = balance
            bot_state["latest_data"]["positions"] = positions
        except Exception as e:
            add_system_log(f"Error fetching live portfolio data: {e}")
            
    return {
        "balance": bot_state["latest_data"]["balance"],
        "positions": bot_state["latest_data"]["positions"]
    }

@app.get("/api/history")
def get_history():
    return {
        "logs": bot_state["latest_data"]["logs"],
        "trades": bot_state["latest_data"]["trades"]
    }

signals_cache = {
    "data": [],
    "last_updated": 0.0
}

def fetch_single_signal(symbol, client, sma_strat, rsi_strat, hybrid_strat, vol_ema_strat):
    import pandas as pd
    try:
        df = client.get_bars(symbol=symbol, interval=Config.CANDLE_PERIOD, limit=100)
        if df.empty:
            return {
                "symbol": symbol,
                "price": 0.0,
                "rsi": 0.0,
                "sma_fast": 0.0,
                "sma_slow": 0.0,
                "sma_signal": "N/A",
                "rsi_signal": "N/A",
                "hybrid_signal": "N/A",
                "volume_ema_signal": "N/A"
            }
        if Config.CANDLE_PERIOD != "d" and len(df) > 3:
            df = df.iloc[:-1].copy()
        current_price = float(df['close'].iloc[-1])
        # SMA values
        sma_fast_series = df['close'].rolling(window=10).mean()
        sma_slow_series = df['close'].rolling(window=30).mean()
        sma_fast_val = float(sma_fast_series.iloc[-1]) if not pd.isna(sma_fast_series.iloc[-1]) else 0.0
        sma_slow_val = float(sma_slow_series.iloc[-1]) if not pd.isna(sma_slow_series.iloc[-1]) else 0.0
        
        # RSI values
        delta = df['close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-9)
        rsi_series = 100 - (100 / (1 + rs))
        rsi_val = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 0.0
        
        # Strategy signals
        sma_sig = sma_strat.generate_signal(df)
        rsi_sig = rsi_strat.generate_signal(df)
        hybrid_sig = hybrid_strat.generate_signal(df)
        vol_ema_sig = vol_ema_strat.generate_signal(df)
        
        return {
            "symbol": symbol,
            "price": current_price,
            "rsi": round(rsi_val, 2),
            "sma_fast": round(sma_fast_val, 2),
            "sma_slow": round(sma_slow_val, 2),
            "sma_signal": sma_sig,
            "rsi_signal": rsi_sig,
            "hybrid_signal": hybrid_sig,
            "volume_ema_signal": vol_ema_sig
        }
    except Exception as e:
        return {
            "symbol": symbol,
            "price": 0.0,
            "rsi": 0.0,
            "sma_fast": 0.0,
            "sma_slow": 0.0,
            "sma_signal": "ERROR",
            "rsi_signal": "ERROR",
            "hybrid_signal": "ERROR",
            "volume_ema_signal": "ERROR"
        }

@app.get("/api/signals")
def get_signals():
    import time
    import pandas as pd
    from concurrent.futures import ThreadPoolExecutor
    
    # Check if cache is fresh (10 seconds)
    current_time = time.time()
    if signals_cache["data"] and (current_time - signals_cache["last_updated"] < 10.0):
        return signals_cache["data"]
        
    from strategies.sma_crossover import SMACrossoverStrategy
    from strategies.rsi_strategy import RSIStrategy
    from strategies.hybrid_strategy import SmaRsiHybridStrategy
    from strategies.volume_ema_breakout import VolumeEmaBreakoutStrategy
    
    sma_strat = SMACrossoverStrategy(fast_period=10, slow_period=30)
    rsi_strat = RSIStrategy(period=14, oversold=30.0, overbought=70.0)
    hybrid_strat = SmaRsiHybridStrategy(fast_period=10, slow_period=30, rsi_period=14, oversold=40.0, overbought=60.0)
    vol_ema_strat = VolumeEmaBreakoutStrategy(fast_period=9, slow_period=21, vol_period=20, vol_factor=2.5)
    
    client = bot_state["client"]
    if not client:
        from clients.local_paper import LocalPaperTradingClient
        client = LocalPaperTradingClient(initial_cash=10000.0, portfolio_file="local_portfolio.json")
        
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(fetch_single_signal, symbol, client, sma_strat, rsi_strat, hybrid_strat, vol_ema_strat)
            for symbol in Config.DEFAULT_SYMBOLS
        ]
        signals_data = [f.result() for f in futures]
        
    signals_cache["data"] = signals_data
    signals_cache["last_updated"] = current_time
    
    return signals_data

@app.post("/api/start")
def start_bot(market: Optional[str] = "us"):
    market = (market or "us").lower()
    if market == "hk":
        if bot_state["running_hk"]:
            return {"status": "already running", "message": "HK Bot is already running."}
        if not bot_state["bot_hk"]:
            success, msg = init_bot_components()
            if not success:
                raise HTTPException(status_code=400, detail=f"Cannot start HK bot: {msg}")
        bot_state["running_hk"] = True
        add_system_log("HK Bot trading loop started by user.")
        return {"status": "started", "message": "HK Trading bot successfully started."}
    else:
        if bot_state["running_us"]:
            return {"status": "already running", "message": "US Bot is already running."}
        if not bot_state["bot_us"]:
            success, msg = init_bot_components()
            if not success:
                raise HTTPException(status_code=400, detail=f"Cannot start US bot: {msg}")
        bot_state["running_us"] = True
        add_system_log("US Bot trading loop started by user.")
        return {"status": "started", "message": "US Trading bot successfully started."}

@app.post("/api/stop")
def stop_bot(market: Optional[str] = "us"):
    market = (market or "us").lower()
    if market == "hk":
        if not bot_state["running_hk"]:
            return {"status": "already stopped", "message": "HK Bot is already idle."}
        bot_state["running_hk"] = False
        add_system_log("HK Bot trading loop stopped by user.")
        return {"status": "stopped", "message": "HK Trading bot successfully stopped."}
    else:
        if not bot_state["running_us"]:
            return {"status": "already stopped", "message": "US Bot is already idle."}
        bot_state["running_us"] = False
        add_system_log("US Bot trading loop stopped by user.")
        return {"status": "stopped", "message": "US Trading bot successfully stopped."}

@app.post("/api/config")
def update_config(data: ConfigModel):
    global config_lock, Config
    with config_lock:
        try:
            # Force reload values from .env first to catch any manual external edits (e.g. credentials)
            Config.reload_values()
            
            # Overwrite .env file
            with open(".env", "w", encoding="utf-8") as f:
                f.write(f"TRADE_MODE={data.trade_mode.upper()}\n\n")
                
                # Maintain credentials (use new ones if supplied, else keep current)
                username = data.username if data.username else Config.WEBULL_USERNAME
                password = data.password if data.password else Config.WEBULL_PASSWORD
                trade_pin = data.trade_pin if data.trade_pin else Config.WEBULL_TRADE_PIN
                app_key = data.app_key if data.app_key else Config.WEBULL_APP_KEY
                app_secret = data.app_secret if data.app_secret else Config.WEBULL_APP_SECRET
                
                f.write(f"WEBULL_USERNAME={username}\n")
                f.write(f"WEBULL_PASSWORD={password}\n")
                f.write(f"WEBULL_TRADE_PIN={trade_pin}\n")
                f.write("WEBULL_DEVICE_NAME=PythonBot\n\n")
                
                f.write(f"WEBULL_APP_KEY={app_key}\n")
                f.write(f"WEBULL_APP_SECRET={app_secret}\n")
                api_endpoint = data.webull_api_endpoint if data.webull_api_endpoint else Config.WEBULL_API_ENDPOINT
                api_region = data.webull_api_region if data.webull_api_region else Config.WEBULL_API_REGION
                f.write(f"WEBULL_API_ENDPOINT={api_endpoint}\n")
                f.write(f"WEBULL_API_REGION={api_region.lower()}\n\n")
                
                symbols_str = ",".join(data.symbols).upper()
                f.write(f"DEFAULT_SYMBOLS={symbols_str}\n")
                f.write(f"TRADE_QUANTITY={data.quantity}\n")
                qty_hk = data.quantity_hk if data.quantity_hk is not None else 100
                f.write(f"TRADE_QUANTITY_HK={qty_hk}\n")
                f.write(f"HK_TRADE_BUDGET_HKD={Config.HK_TRADE_BUDGET_HKD}\n")
                f.write(f"HK_ETF_BUDGET_HKD={Config.HK_ETF_BUDGET_HKD}\n")
                f.write(f"HK_DEFAULT_BOARD_LOT={Config.HK_DEFAULT_BOARD_LOT}\n")
                
                hk_max_slots = data.hk_max_slots if data.hk_max_slots is not None else Config.HK_MAX_SLOTS
                hk_max_price_per_slot = data.hk_max_price_per_slot if data.hk_max_price_per_slot is not None else Config.HK_MAX_PRICE_PER_SLOT
                hk_max_qty_per_slot = data.hk_max_qty_per_slot if data.hk_max_qty_per_slot is not None else Config.HK_MAX_QTY_PER_SLOT
                hk_filter_price_limit = data.hk_filter_price_limit if data.hk_filter_price_limit is not None else Config.HK_FILTER_PRICE_LIMIT
                hk_filter_price_operator = data.hk_filter_price_operator if data.hk_filter_price_operator is not None else Config.HK_FILTER_PRICE_OPERATOR
                
                f.write(f"HK_MAX_SLOTS={hk_max_slots}\n")
                f.write(f"HK_MAX_PRICE_PER_SLOT={hk_max_price_per_slot}\n")
                f.write(f"HK_MAX_QTY_PER_SLOT={hk_max_qty_per_slot}\n")
                f.write(f"HK_FILTER_PRICE_LIMIT={hk_filter_price_limit}\n")
                f.write(f"HK_FILTER_PRICE_OPERATOR={hk_filter_price_operator}\n")
                
                strategy_us = data.strategy_us if data.strategy_us else (data.strategy if data.strategy else Config.STRATEGY_US)
                strategy_hk = data.strategy_hk if data.strategy_hk else (data.strategy if data.strategy else Config.STRATEGY_HK)
                f.write(f"STRATEGY_US={strategy_us.lower()}\n")
                f.write(f"STRATEGY_HK={strategy_hk.lower()}\n")
                f.write(f"HK_SMA_FAST_PERIOD={Config.HK_SMA_FAST_PERIOD}\n")
                f.write(f"HK_SMA_SLOW_PERIOD={Config.HK_SMA_SLOW_PERIOD}\n")
                
                f.write(f"INTERVAL={data.interval}\n")
                f.write(f"CANDLE_PERIOD={data.candle_period.lower()}\n")
                sim_cash_hkd = data.simulated_initial_cash_hkd if data.simulated_initial_cash_hkd is not None else Config.SIMULATED_INITIAL_CASH_HKD
                sim_cash = sim_cash_hkd / Config.USD_HKD_RATE
                f.write(f"SIMULATED_INITIAL_CASH={sim_cash}\n")
                f.write(f"SIMULATED_INITIAL_CASH_HKD={sim_cash_hkd}\n")
                f.write(f"USD_HKD_RATE={Config.USD_HKD_RATE}\n")
                # HK Risk Management
                hk_sl = data.hk_stop_loss_pct if data.hk_stop_loss_pct is not None else Config.HK_STOP_LOSS_PCT
                hk_tp = data.hk_take_profit_pct if data.hk_take_profit_pct is not None else Config.HK_TAKE_PROFIT_PCT
                hk_trail = data.hk_trailing_stop_pct if data.hk_trailing_stop_pct is not None else Config.HK_TRAILING_STOP_PCT
                hk_hold = data.hk_max_hold_days if data.hk_max_hold_days is not None else Config.HK_MAX_HOLD_DAYS
                hk_daily = data.hk_daily_loss_limit_hkd if data.hk_daily_loss_limit_hkd is not None else Config.HK_DAILY_LOSS_LIMIT_HKD
                f.write(f"\n# HK Risk Management\n")
                f.write(f"HK_STOP_LOSS_PCT={hk_sl}\n")
                f.write(f"HK_TAKE_PROFIT_PCT={hk_tp}\n")
                f.write(f"HK_TRAILING_STOP_PCT={hk_trail}\n")
                f.write(f"HK_MAX_HOLD_DAYS={hk_hold}\n")
                f.write(f"HK_DAILY_LOSS_LIMIT_HKD={hk_daily}\n")

                # HK ETF Settings
                hk_etf_qty = data.hk_etf_trade_qty if data.hk_etf_trade_qty is not None else Config.HK_ETF_TRADE_QTY
                hk_etf_sl = data.hk_etf_stop_loss_pct if data.hk_etf_stop_loss_pct is not None else Config.HK_ETF_STOP_LOSS_PCT
                hk_etf_tp = data.hk_etf_take_profit_pct if data.hk_etf_take_profit_pct is not None else Config.HK_ETF_TAKE_PROFIT_PCT
                hk_etf_strat = data.hk_etf_strategy if data.hk_etf_strategy is not None else Config.HK_ETF_STRATEGY
                f.write(f"\n# HK ETF Settings\n")
                auto_long = data.hk_auto_long if data.hk_auto_long is not None else Config.HK_AUTO_LONG
                etf_hedging = data.enable_inverse_etf_hedging if data.enable_inverse_etf_hedging is not None else Config.ENABLE_INVERSE_ETF_HEDGING
                f.write(f"HK_ETF_TRADE_QTY={hk_etf_qty}\n")
                f.write(f"HK_ETF_STOP_LOSS_PCT={hk_etf_sl}\n")
                f.write(f"HK_ETF_TAKE_PROFIT_PCT={hk_etf_tp}\n")
                f.write(f"HK_ETF_STRATEGY={hk_etf_strat.lower()}\n")
                f.write(f"HK_SHORT_BEARISH_THRESHOLD={Config.HK_SHORT_BEARISH_THRESHOLD}\n")
                f.write(f"HK_SHORT_EXIT_THRESHOLD={Config.HK_SHORT_EXIT_THRESHOLD}\n")
                f.write(f"HK_AUTO_LONG={str(auto_long).upper()}\n")
                f.write(f"ENABLE_INVERSE_ETF_HEDGING={str(etf_hedging).upper()}\n")
                
                # US ETF Settings
                us_auto_long = data.us_auto_long if data.us_auto_long is not None else Config.US_AUTO_LONG
                us_etf_hedging = data.us_enable_inverse_etf_hedging if data.us_enable_inverse_etf_hedging is not None else Config.US_ENABLE_INVERSE_ETF_HEDGING
                us_etf_budget = data.us_etf_budget if data.us_etf_budget is not None else Config.US_ETF_BUDGET
                us_etf_strategy = data.us_etf_strategy if data.us_etf_strategy is not None else Config.US_ETF_STRATEGY
                f.write(f"\n# US ETF Settings\n")
                f.write(f"US_AUTO_LONG={str(us_auto_long).upper()}\n")
                f.write(f"US_ENABLE_INVERSE_ETF_HEDGING={str(us_etf_hedging).upper()}\n")
                f.write(f"US_ETF_BUDGET={us_etf_budget}\n")
                f.write(f"US_ETF_STRATEGY={us_etf_strategy.lower()}\n")
            
                us_sl = data.us_stop_loss_pct if data.us_stop_loss_pct is not None else Config.US_STOP_LOSS_PCT
                us_tp = data.us_take_profit_pct if data.us_take_profit_pct is not None else Config.US_TAKE_PROFIT_PCT
                us_trail = data.us_trailing_stop_pct if data.us_trailing_stop_pct is not None else Config.US_TRAILING_STOP_PCT
                us_hold = data.us_max_hold_days if data.us_max_hold_days is not None else Config.US_MAX_HOLD_DAYS
                us_daily = data.us_daily_loss_limit_usd if data.us_daily_loss_limit_usd is not None else Config.US_DAILY_LOSS_LIMIT_USD
                us_etf_sl = data.us_etf_stop_loss_pct if data.us_etf_stop_loss_pct is not None else Config.US_ETF_STOP_LOSS_PCT
                us_etf_tp = data.us_etf_take_profit_pct if data.us_etf_take_profit_pct is not None else Config.US_ETF_TAKE_PROFIT_PCT
                us_etf_trail = data.us_etf_trailing_stop_pct if data.us_etf_trailing_stop_pct is not None else Config.US_ETF_TRAILING_STOP_PCT
                f.write(f"US_STOP_LOSS_PCT={us_sl}\nUS_TAKE_PROFIT_PCT={us_tp}\nUS_TRAILING_STOP_PCT={us_trail}\nUS_MAX_HOLD_DAYS={us_hold}\nUS_DAILY_LOSS_LIMIT_USD={us_daily}\nUS_ETF_STOP_LOSS_PCT={us_etf_sl}\nUS_ETF_TAKE_PROFIT_PCT={us_etf_tp}\nUS_ETF_TRAILING_STOP_PCT={us_etf_trail}\nREGULAR_HOURS_ONLY=TRUE\nUS_MIN_ORDER_VALUE=1.0\n")
                f.write(f"US_ALLOW_NAKED_INVERSE={str(Config.US_ALLOW_NAKED_INVERSE).upper()}\nUS_HEDGE_RATIO={Config.US_HEDGE_RATIO}\nPAPER_SLIPPAGE_BPS={Config.PAPER_SLIPPAGE_BPS}\nPAPER_FEE_USD={Config.PAPER_FEE_USD}\nPAPER_FEE_HK_RATE={Config.PAPER_FEE_HK_RATE}\n")
            # Force reload Config in-place
            Config.reload_values()
            
            add_system_log("Configuration updated. Reinitializing bot components...")
            
            # If bot was running, stop it first
            was_running_us = bot_state["running_us"]
            was_running_hk = bot_state["running_hk"]
            bot_state["running_us"] = False
            bot_state["running_hk"] = False
            
            # Re-init
            success, msg = init_bot_components()
            if not success:
                raise HTTPException(status_code=400, detail=f"Configuration saved, but reinitialization failed: {msg}")
                
            # If TRADE_MODE is LOCAL_PAPER, reset the portfolio cash to the newly saved values
            if Config.TRADE_MODE == "LOCAL_PAPER" and bot_state["client"]:
                client = bot_state["client"]
                if hasattr(client, "portfolio") and "balance" in client.portfolio:
                    client.portfolio["balance"]["cash_hkd"] = Config.SIMULATED_INITIAL_CASH_HKD
                    client.portfolio["balance"]["cash"] = Config.SIMULATED_INITIAL_CASH_HKD / Config.USD_HKD_RATE
                    client._save_portfolio()
                    add_system_log(f"Simulated cash balances updated to USD: {Config.SIMULATED_INITIAL_CASH}, HKD: {Config.SIMULATED_INITIAL_CASH_HKD}")
                
            # Restore running state if possible
            if was_running_us:
                bot_state["running_us"] = True
            if was_running_hk:
                bot_state["running_hk"] = True
            add_system_log("Bot running states restored.")
                
            return {"status": "success", "message": "Configuration updated and applied successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating config: {str(e)}")

@app.post("/api/order")
def place_manual_order(order: OrderModel):
    if not bot_state["client"]:
        raise HTTPException(status_code=400, detail="Client is not authenticated. Please check configuration.")
        
    try:
        add_system_log(f"Manual order request received: {order.action} {order.qty} {order.symbol}")
        res = bot_state["client"].place_order(
            symbol=order.symbol,
            qty=order.qty,
            action=order.action,
            order_type=order.order_type,
            price=order.price
        )
        
        if res.get("status") in ["FILLED", "SUBMITTED"]:
            exec_price = res.get("price") or "Market Price"
            add_system_log(f"Manual order successful: {order.action} {order.qty} {order.symbol} @ {exec_price}")
            
            # Add to trades list
            from datetime import datetime
            bot_state["latest_data"]["trades"].append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "symbol": order.symbol.upper(),
                "action": order.action.upper(),
                "qty": order.qty,
                "price": res.get("price", 0.0),
                "status": res.get("status")
            })
            
            # Trigger a background update of portfolio data
            try:
                bot_state["latest_data"]["balance"] = bot_state["client"].get_account_balance()
                bot_state["latest_data"]["positions"] = bot_state["client"].get_positions()
            except Exception:
                pass
                
            return {"status": "success", "detail": res}
        else:
            raise HTTPException(status_code=400, detail=res.get("reason", "Order failed"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order execution error: {str(e)}")

def get_symbol_price(symbol: str) -> float:
    client = bot_state["client"]
    if not client:
        return 0.0
    try:
        if hasattr(client, "_get_current_price"):
            return client._get_current_price(symbol)
        else:
            df = client.get_bars(symbol=symbol, interval="m5", limit=1)
            if not df.empty:
                return float(df['close'].iloc[-1])
    except Exception:
        pass
    return 0.0

@app.get("/api/etf-short-status")
def get_etf_short_status():
    client = bot_state["client"]
    if not client:
        return []
        
    try:
        positions = client.get_positions()
        pos_map = {pos['symbol']: pos for pos in positions}
    except Exception:
        pos_map = {}
        
    result = []
    from concurrent.futures import ThreadPoolExecutor
    
    def process_pair(underlying, etf):
        underlying_price = get_symbol_price(underlying)
        etf_price = get_symbol_price(etf)
        
        pos = pos_map.get(etf)
        owned_qty = pos["qty"] if pos else 0.0
        avg_price = pos["avg_price"] if pos else 0.0
        market_value = owned_qty * etf_price
        unrealized_pnl = market_value - (owned_qty * avg_price) if owned_qty > 0 else 0.0
        
        return {
            "underlying": underlying,
            "underlying_price": underlying_price,
            "etf": etf,
            "etf_price": etf_price,
            "owned_qty": owned_qty,
            "avg_price": avg_price,
            "market_value": market_value,
            "unrealized_pnl": unrealized_pnl
        }
        
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(process_pair, underlying, etf)
            for underlying, etf in Config.INVERSE_ETF_MAP.items()
        ]
        result = [f.result() for f in futures]
        
    return result

if __name__ == "__main__":
    import uvicorn
    # Port 8484 is customized for Python server
    uvicorn.run("server:app", host="127.0.0.1", port=8484, reload=True)
