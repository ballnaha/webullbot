import os
from dotenv import load_dotenv

# Load environment variables from .env file (override=True allows dynamic reload)
load_dotenv(override=True)

class Config:
    # Mode selection: LOCAL_PAPER, WEBULL_PAPER, WEBULL_LIVE, WEBULL_OFFICIAL
    TRADE_MODE = os.getenv("TRADE_MODE", "LOCAL_PAPER").upper()

    # Webull Unofficial API credentials
    WEBULL_USERNAME = os.getenv("WEBULL_USERNAME", "")
    WEBULL_PASSWORD = os.getenv("WEBULL_PASSWORD", "")
    WEBULL_TRADE_PIN = os.getenv("WEBULL_TRADE_PIN", "")
    WEBULL_DEVICE_NAME = os.getenv("WEBULL_DEVICE_NAME", "PythonBot")

    # Webull Official OpenAPI credentials
    WEBULL_APP_KEY = os.getenv("WEBULL_APP_KEY", "")
    WEBULL_APP_SECRET = os.getenv("WEBULL_APP_SECRET", "")

    # Strategy Parameters
    DEFAULT_SYMBOLS = [
        symbol.strip().upper() 
        for symbol in os.getenv("DEFAULT_SYMBOLS", "AAPL,MSFT,TSLA").split(",") 
        if symbol.strip()
    ]
    TRADE_QUANTITY = int(os.getenv("TRADE_QUANTITY", "1"))
    INTERVAL = int(os.getenv("INTERVAL", "60"))
    CANDLE_PERIOD = os.getenv("CANDLE_PERIOD", "m5").lower()

    # Local simulation parameters
    SIMULATED_INITIAL_CASH = float(os.getenv("SIMULATED_INITIAL_CASH", "10000.0"))
    PORTFOLIO_FILE = "local_portfolio.json"

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
