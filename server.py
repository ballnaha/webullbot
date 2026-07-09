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
    "strategy_hk": "sma",
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

def init_bot_components():
    """
    Initializes or re-initializes client and bot based on current Config settings.
    """
    # Validate config first
    ok, msg = Config.validate()
    if not ok:
        add_system_log(f"Configuration validation failed: {msg}")
        return False, msg

    try:
        add_system_log(f"Initializing trading client for mode: {Config.TRADE_MODE}...")
        client = get_client()
        
        # Attempt login
        login_ok = client.login()
        if not login_ok:
            return False, "Failed to login to Webull. Check credentials in settings."
            
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
        else:
            strategy_us = get_strategy("rsi", period=14, oversold=30.0, overbought=70.0)
            
        # Load HK strategy
        add_system_log(f"Loading HK strategy: {Config.STRATEGY_HK}...")
        if Config.STRATEGY_HK == "sma":
            strategy_hk = get_strategy("sma", fast_period=10, slow_period=30)
        elif Config.STRATEGY_HK == "hybrid":
            strategy_hk = get_strategy("hybrid", fast_period=10, slow_period=30, period=14, oversold=40.0, overbought=60.0)
        else:
            strategy_hk = get_strategy("rsi", period=14, oversold=30.0, overbought=70.0)
            
        # Split symbols
        us_symbols = [s for s in Config.DEFAULT_SYMBOLS if not s.endswith(".HK")]
        hk_symbols = [s for s in Config.DEFAULT_SYMBOLS if s.endswith(".HK")]
            
        # Create bot orchestrators
        bot_state["bot_us"] = TradingBot(client=client, strategy=strategy_us, symbols=us_symbols)
        bot_state["bot_hk"] = TradingBot(client=client, strategy=strategy_hk, symbols=hk_symbols)
        add_system_log("Bot components successfully initialized for both US and HK markets!")
        
        # Initial data fetch
        balance = client.get_account_balance()
        positions = client.get_positions()
        bot_state["latest_data"]["balance"] = balance
        bot_state["latest_data"]["positions"] = positions
        
        return True, "Success"
    except Exception as e:
        error_msg = f"Initialization error: {e}"
        add_system_log(error_msg)
        return False, error_msg

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
    quantity: int
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
        "hk_max_slots": Config.HK_MAX_SLOTS,
        "hk_max_price_per_slot": Config.HK_MAX_PRICE_PER_SLOT,
        "hk_max_qty_per_slot": Config.HK_MAX_QTY_PER_SLOT,
        "hk_filter_price_limit": Config.HK_FILTER_PRICE_LIMIT,
        "hk_filter_price_operator": Config.HK_FILTER_PRICE_OPERATOR,
        "interval": Config.INTERVAL,
        "candle_period": Config.CANDLE_PERIOD,
        "simulated_initial_cash": Config.SIMULATED_INITIAL_CASH,
        "simulated_initial_cash_hkd": Config.SIMULATED_INITIAL_CASH_HKD,
        "has_client": bot_state["client"] is not None
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

def fetch_single_signal(symbol, client, sma_strat, rsi_strat, hybrid_strat):
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
                "hybrid_signal": "N/A"
            }
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
        
        return {
            "symbol": symbol,
            "price": current_price,
            "rsi": round(rsi_val, 2),
            "sma_fast": round(sma_fast_val, 2),
            "sma_slow": round(sma_slow_val, 2),
            "sma_signal": sma_sig,
            "rsi_signal": rsi_sig,
            "hybrid_signal": hybrid_sig
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
            "hybrid_signal": "ERROR"
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
    
    sma_strat = SMACrossoverStrategy(fast_period=10, slow_period=30)
    rsi_strat = RSIStrategy(period=14, oversold=30.0, overbought=70.0)
    hybrid_strat = SmaRsiHybridStrategy(fast_period=10, slow_period=30, rsi_period=14, oversold=40.0, overbought=60.0)
    
    client = bot_state["client"]
    if not client:
        from clients.local_paper import LocalPaperTradingClient
        client = LocalPaperTradingClient(initial_cash=10000.0, portfolio_file="local_portfolio.json")
        
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(fetch_single_signal, symbol, client, sma_strat, rsi_strat, hybrid_strat)
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
                
                f.write(f"INTERVAL={data.interval}\n")
                f.write(f"CANDLE_PERIOD={data.candle_period.lower()}\n")
                sim_cash = data.simulated_initial_cash if data.simulated_initial_cash is not None else Config.SIMULATED_INITIAL_CASH
                sim_cash_hkd = data.simulated_initial_cash_hkd if data.simulated_initial_cash_hkd is not None else Config.SIMULATED_INITIAL_CASH_HKD
                f.write(f"SIMULATED_INITIAL_CASH={sim_cash}\n")
                f.write(f"SIMULATED_INITIAL_CASH_HKD={sim_cash_hkd}\n")
            
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
                    client.portfolio["balance"]["cash"] = Config.SIMULATED_INITIAL_CASH
                    client.portfolio["balance"]["cash_hkd"] = Config.SIMULATED_INITIAL_CASH_HKD
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

if __name__ == "__main__":
    import uvicorn
    # Port 8484 is customized for Python server
    uvicorn.run("server:app", host="127.0.0.1", port=8484, reload=True)
