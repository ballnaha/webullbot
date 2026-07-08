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
    "running": False,
    "bot": None,
    "client": None,
    "strategy_name": "sma",
    "latest_data": {
        "balance": {"cash": 0.0, "net_liquidation": 0.0, "unrealized_pnl": 0.0, "currency": "USD"},
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
        
        # Load strategy
        add_system_log(f"Loading strategy: {bot_state['strategy_name']}...")
        if bot_state["strategy_name"] == "sma":
            strategy = get_strategy("sma", fast_period=10, slow_period=30)
        elif bot_state["strategy_name"] == "hybrid":
            strategy = get_strategy("hybrid", fast_period=10, slow_period=30, period=14, oversold=40.0, overbought=60.0)
        else:
            strategy = get_strategy("rsi", period=14, oversold=30.0, overbought=70.0)
            
        # Create bot orchestrator
        bot_state["bot"] = TradingBot(client=client, strategy=strategy, symbols=Config.DEFAULT_SYMBOLS)
        add_system_log("Bot components successfully initialized!")
        
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
        if bot_state["running"]:
            if bot_state["bot"]:
                try:
                    add_system_log("Executing background bot trade scan...")
                    # run_once returns updated state
                    res = bot_state["bot"].run_once()
                    
                    # Update local state cache
                    bot_state["latest_data"]["balance"] = res["balance"]
                    bot_state["latest_data"]["positions"] = res["positions"]
                    
                    # Merge logs
                    for log in res["logs"]:
                        if log not in bot_state["latest_data"]["logs"]:
                            bot_state["latest_data"]["logs"].append(log)
                            
                    # Keep logs capped
                    if len(bot_state["latest_data"]["logs"]) > 100:
                        bot_state["latest_data"]["logs"] = bot_state["latest_data"]["logs"][-100:]
                        
                    bot_state["latest_data"]["trades"] = res["trades"]
                except Exception as e:
                    add_system_log(f"Error in trading loop: {e}")
            else:
                add_system_log("Warning: Bot is active but bot instance is None. Attempting reinitialization...")
                success, _ = init_bot_components()
                if not success:
                    add_system_log("Reinitialization failed. Stopping bot.")
                    bot_state["running"] = False
                    
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
    interval: int
    candle_period: str
    strategy: str
    # Credentials optional updates
    username: Optional[str] = ""
    password: Optional[str] = ""
    trade_pin: Optional[str] = ""
    app_key: Optional[str] = ""
    app_secret: Optional[str] = ""

class OrderModel(BaseModel):
    symbol: str
    qty: float
    action: str  # BUY or SELL
    order_type: str = "MKT"  # MKT or LMT
    price: Optional[float] = None

@app.get("/api/status")
def get_status():
    return {
        "running": bot_state["running"],
        "trade_mode": Config.TRADE_MODE,
        "strategy": bot_state["strategy_name"],
        "symbols": Config.DEFAULT_SYMBOLS,
        "quantity": Config.TRADE_QUANTITY,
        "quantity_hk": Config.TRADE_QUANTITY_HK,
        "interval": Config.INTERVAL,
        "candle_period": Config.CANDLE_PERIOD,
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
def start_bot():
    if bot_state["running"]:
        return {"status": "already running", "message": "Bot is already running."}
        
    # Check if bot components are initialized, otherwise try initialization
    if not bot_state["bot"]:
        success, msg = init_bot_components()
        if not success:
            raise HTTPException(status_code=400, detail=f"Cannot start bot: {msg}")
            
    bot_state["running"] = True
    add_system_log("Bot trading loop started by user.")
    return {"status": "started", "message": "Trading bot successfully started."}

@app.post("/api/stop")
def stop_bot():
    if not bot_state["running"]:
        return {"status": "already stopped", "message": "Bot is already idle."}
        
    bot_state["running"] = False
    add_system_log("Bot trading loop stopped by user.")
    return {"status": "stopped", "message": "Trading bot successfully stopped."}

@app.post("/api/config")
def update_config(data: ConfigModel):
    global config_lock, Config
    with config_lock:
        try:
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
                f.write(f"WEBULL_APP_SECRET={app_secret}\n\n")
                
                symbols_str = ",".join(data.symbols).upper()
                f.write(f"DEFAULT_SYMBOLS={symbols_str}\n")
                f.write(f"TRADE_QUANTITY={data.quantity}\n")
                qty_hk = data.quantity_hk if data.quantity_hk is not None else 100
                f.write(f"TRADE_QUANTITY_HK={qty_hk}\n")
                f.write(f"INTERVAL={data.interval}\n")
                f.write(f"CANDLE_PERIOD={data.candle_period.lower()}\n")
                f.write(f"SIMULATED_INITIAL_CASH={Config.SIMULATED_INITIAL_CASH}\n")
            
            # Force reload Config in-place
            Config.reload_values()
            
            # Update strategy name state
            bot_state["strategy_name"] = data.strategy.lower()
            
            add_system_log("Configuration updated. Reinitializing bot components...")
            
            # If bot was running, stop it first
            was_running = bot_state["running"]
            bot_state["running"] = False
            
            # Re-init
            success, msg = init_bot_components()
            if not success:
                raise HTTPException(status_code=400, detail=f"Configuration saved, but reinitialization failed: {msg}")
                
            # Restore running state if possible
            if was_running:
                bot_state["running"] = True
                add_system_log("Bot running state restored.")
                
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
