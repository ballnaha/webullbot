import os
from dotenv import load_dotenv

# Load environment variables from .env file (override=True allows dynamic reload)
load_dotenv(override=True)

class Config:
    # Mode selection: LOCAL_PAPER, WEBULL_PAPER, WEBULL_LIVE, WEBULL_OFFICIAL
    TRADE_MODE = "LOCAL_PAPER"
    WEBULL_USERNAME = ""
    WEBULL_PASSWORD = ""
    WEBULL_TRADE_PIN = ""
    WEBULL_DEVICE_NAME = "PythonBot"
    WEBULL_APP_KEY = ""
    WEBULL_APP_SECRET = ""
    WEBULL_API_ENDPOINT = ""
    WEBULL_API_REGION = "us"
    DEFAULT_SYMBOLS = []
    TRADE_QUANTITY = 1
    TRADE_QUANTITY_HK = 100
    HK_MAX_SLOTS = 1
    HK_MAX_PRICE_PER_SLOT = 999999.0
    HK_MAX_QTY_PER_SLOT = 100
    HK_FILTER_PRICE_LIMIT = 20.0
    HK_FILTER_PRICE_OPERATOR = "le"
    INTERVAL = 60
    CANDLE_PERIOD = "m5"
    STRATEGY_US = "sma"
    STRATEGY_HK = "sma"
    SIMULATED_INITIAL_CASH = 10000.0
    SIMULATED_INITIAL_CASH_HKD = 78000.0
    PORTFOLIO_FILE = "local_portfolio.json"
    
    # Inverse ETF hedging configurations
    ENABLE_INVERSE_ETF_HEDGING = True
    INVERSE_ETF_MAP = {
        "AAPL": "AAPD",        # 1.5x Short Apple
        "TSLA": "TSLQ",        # 1x Short Tesla
        "NVDA": "NVDS",        # 1.25x Short Nvidia
        "MSFT": "MSFD",        # 1.5x Short Microsoft
        "QQQ": "SQQQ",         # 3x Short Nasdaq-100
        "SPY": "SPXS",         # 3x Short S&P 500
        "0700.HK": "7500.HK",  # Hedge Tencent via Short Hang Seng Index
        "9988.HK": "7500.HK",  # Hedge Alibaba via Short Hang Seng Index
        "1810.HK": "7552.HK",  # Hedge Xiaomi via Short Hang Seng Tech Index
        "3690.HK": "7552.HK",  # Hedge Meituan via Short Hang Seng Tech Index
    }

    @classmethod
    def reload_values(cls):
        """
        Reload values from environment variables in-place to update references correctly
        after configuration changes.
        """
        load_dotenv(override=True)
        cls.TRADE_MODE = os.getenv("TRADE_MODE", "LOCAL_PAPER").upper()
        cls.WEBULL_USERNAME = os.getenv("WEBULL_USERNAME", "")
        cls.WEBULL_PASSWORD = os.getenv("WEBULL_PASSWORD", "")
        cls.WEBULL_TRADE_PIN = os.getenv("WEBULL_TRADE_PIN", "")
        cls.WEBULL_DEVICE_NAME = os.getenv("WEBULL_DEVICE_NAME", "PythonBot")
        cls.WEBULL_APP_KEY = os.getenv("WEBULL_APP_KEY", "")
        cls.WEBULL_APP_SECRET = os.getenv("WEBULL_APP_SECRET", "")
        cls.WEBULL_API_ENDPOINT = os.getenv("WEBULL_API_ENDPOINT", "")
        cls.WEBULL_API_REGION = os.getenv("WEBULL_API_REGION", "us").lower()
        cls.DEFAULT_SYMBOLS = [
            symbol.strip().upper() 
            for symbol in os.getenv("DEFAULT_SYMBOLS", "").split(",") 
            if symbol.strip()
        ]
        cls.TRADE_QUANTITY = int(os.getenv("TRADE_QUANTITY", "1"))
        cls.TRADE_QUANTITY_HK = int(os.getenv("TRADE_QUANTITY_HK", "100"))
        cls.HK_MAX_SLOTS = int(os.getenv("HK_MAX_SLOTS", "1"))
        cls.HK_MAX_PRICE_PER_SLOT = float(os.getenv("HK_MAX_PRICE_PER_SLOT", "999999.0"))
        cls.HK_MAX_QTY_PER_SLOT = int(os.getenv("HK_MAX_QTY_PER_SLOT", "100"))
        cls.HK_FILTER_PRICE_LIMIT = float(os.getenv("HK_FILTER_PRICE_LIMIT", "20.0"))
        cls.HK_FILTER_PRICE_OPERATOR = os.getenv("HK_FILTER_PRICE_OPERATOR", "le").lower()
        cls.INTERVAL = int(os.getenv("INTERVAL", "60"))
        cls.CANDLE_PERIOD = os.getenv("CANDLE_PERIOD", "m5").lower()
        cls.STRATEGY_US = os.getenv("STRATEGY_US", "sma").lower()
        cls.STRATEGY_HK = os.getenv("STRATEGY_HK", "sma").lower()
        cls.SIMULATED_INITIAL_CASH = float(os.getenv("SIMULATED_INITIAL_CASH", "10000.0"))
        cls.SIMULATED_INITIAL_CASH_HKD = float(os.getenv("SIMULATED_INITIAL_CASH_HKD", str(cls.SIMULATED_INITIAL_CASH * 7.8)))
        cls.ENABLE_INVERSE_ETF_HEDGING = os.getenv("ENABLE_INVERSE_ETF_HEDGING", "TRUE").upper() == "TRUE"

    @classmethod
    def validate(cls):
        """
        Validate config according to the selected trade mode.
        Returns a tuple (bool, message)
        """
        if cls.TRADE_MODE == "LOCAL_PAPER":
            return True, "LOCAL_PAPER mode loaded successfully. No credentials needed."
        
        if cls.TRADE_MODE in ["WEBULL_PAPER", "WEBULL_LIVE"]:
            if not cls.WEBULL_USERNAME or not cls.WEBULL_PASSWORD:
                return False, f"Username/Password required for {cls.TRADE_MODE} mode."
            if cls.TRADE_MODE == "WEBULL_LIVE" and not cls.WEBULL_TRADE_PIN:
                return False, "Trading PIN is required for live trading."
            return True, f"{cls.TRADE_MODE} configuration looks valid."
        
        if cls.TRADE_MODE == "WEBULL_OFFICIAL":
            if not cls.WEBULL_APP_KEY or not cls.WEBULL_APP_SECRET:
                return False, "App Key and Secret are required for WEBULL_OFFICIAL OpenAPI mode."
            return True, "Official OpenAPI configuration looks valid."
        
        return False, f"Unknown TRADE_MODE: {cls.TRADE_MODE}"

# Run reload initially to load the values on startup
Config.reload_values()
