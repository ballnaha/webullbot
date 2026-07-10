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

    # ── HK Risk Management ──────────────────────────────────────────────────────
    # Stop Loss: ตัดขาดทุนเมื่อราคาร่วงเกิน % จากต้นทุน (0 = ปิดใช้งาน)
    HK_STOP_LOSS_PCT = 5.0
    # Take Profit: ทำกำไรเมื่อราคาขึ้นเกิน % จากต้นทุน (0 = ปิดใช้งาน)
    HK_TAKE_PROFIT_PCT = 8.0
    # Trailing Stop: SL แบบลอยตาม peak ราคา (0 = ปิดใช้งาน)
    HK_TRAILING_STOP_PCT = 0.0
    # Max Hold Days: บังคับขายถ้าถือเกิน N วัน (0 = ปิดใช้งาน)
    HK_MAX_HOLD_DAYS = 0
    # Daily Loss Limit: หยุด HK bot วันนั้นถ้าขาดทุนเกิน N HKD (0 = ปิดใช้งาน)
    HK_DAILY_LOSS_LIMIT_HKD = 0.0
    HK_AUTO_LONG = True
    
    # US ETF Settings
    US_AUTO_LONG = True
    US_ENABLE_INVERSE_ETF_HEDGING = True
    US_ETF_BUDGET = 300.0
    US_ETF_STRATEGY = "standard"
    
    # HK ETF Settings
    HK_ETF_TRADE_QTY = 100
    HK_ETF_STOP_LOSS_PCT = 5.0
    HK_ETF_TAKE_PROFIT_PCT = 8.0
    HK_ETF_STRATEGY = "all"
    
    # Inverse ETF hedging configurations
    ENABLE_INVERSE_ETF_HEDGING = True
    INVERSE_ETF_MAP = {
        "AAPL": "AAPD",        # 1.5x Short Apple
        "TSLA": "TSLQ",        # 1x Short Tesla
        "NVDA": "NVDS",        # 1.25x Short Nvidia
        "MSFT": "MSFD",        # 1.5x Short Microsoft
        "AMZN": "AMZD",        # 1x Short Amazon
        "GOOGL": "GGLD",       # 1x Short Google
        "META": "METD",        # 1x Short Meta
        "NFLX": "NFLD",        # 1x Short Netflix
        "AMD": "AMDS",         # 1x Short AMD
        "AVGO": "AVGD",        # 1x Short Broadcom
        "QQQ": "SQQQ",         # 3x Short Nasdaq-100
        "SPY": "SPXS",         # 3x Short S&P 500
        "SMH": "SOXS",         # 3x Short Semiconductors
        "SOXX": "SOXS",        # 3x Short Semiconductors
        "ARKK": "SARK",        # 1x Short ARK Innovation
        "IWM": "TZA",          # 3x Short Russell 2000
        "XLF": "FAZ",          # 3x Short Financials
        "XLE": "ERY",          # 2x Short Energy
        "GDX": "DUST",         # 2x Short Gold Miners
        "DIA": "SDOW",         # 3x Short Dow Jones
        
        # Hong Kong Mappings to HSI/HSTECH Inverse ETFs
        "0700.HK": "7500.HK",  # Tencent -> 2x Short HSI
        "9988.HK": "7500.HK",  # Alibaba -> 2x Short HSI
        "2318.HK": "7500.HK",  # Ping An -> 2x Short HSI
        "0388.HK": "7500.HK",  # HKEX -> 2x Short HSI
        "1299.HK": "7500.HK",  # AIA -> 2x Short HSI
        "0005.HK": "7500.HK",  # HSBC -> 2x Short HSI
        "0941.HK": "7500.HK",  # China Mobile -> 2x Short HSI
        "3988.HK": "7500.HK",  # Bank of China -> 2x Short HSI
        
        "1810.HK": "7552.HK",  # Xiaomi -> 2x Short HSTECH
        "3690.HK": "7552.HK",  # Meituan -> 2x Short HSTECH
        "9618.HK": "7552.HK",  # JD.com -> 2x Short HSTECH
        "1024.HK": "7552.HK",  # Kuaishou -> 2x Short HSTECH
        "9888.HK": "7552.HK",  # Baidu -> 2x Short HSTECH
        "2015.HK": "7552.HK",  # Li Auto -> 2x Short HSTECH
        "1211.HK": "7552.HK",  # BYD -> 2x Short HSTECH
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
        # HK Risk Management
        cls.HK_STOP_LOSS_PCT = float(os.getenv("HK_STOP_LOSS_PCT", "5.0"))
        cls.HK_TAKE_PROFIT_PCT = float(os.getenv("HK_TAKE_PROFIT_PCT", "8.0"))
        cls.HK_TRAILING_STOP_PCT = float(os.getenv("HK_TRAILING_STOP_PCT", "0.0"))
        cls.HK_MAX_HOLD_DAYS = int(os.getenv("HK_MAX_HOLD_DAYS", "0"))
        cls.HK_DAILY_LOSS_LIMIT_HKD = float(os.getenv("HK_DAILY_LOSS_LIMIT_HKD", "0.0"))
        cls.HK_AUTO_LONG = os.getenv("HK_AUTO_LONG", "TRUE").upper() == "TRUE"
        cls.US_AUTO_LONG = os.getenv("US_AUTO_LONG", "TRUE").upper() == "TRUE"
        cls.US_ENABLE_INVERSE_ETF_HEDGING = os.getenv("US_ENABLE_INVERSE_ETF_HEDGING", "TRUE").upper() == "TRUE"
        cls.US_ETF_BUDGET = float(os.getenv("US_ETF_BUDGET", "300.0"))
        cls.US_ETF_STRATEGY = os.getenv("US_ETF_STRATEGY", "standard").lower()
        cls.ENABLE_INVERSE_ETF_HEDGING = os.getenv("ENABLE_INVERSE_ETF_HEDGING", "TRUE").upper() == "TRUE"
        # HK ETF Settings
        cls.HK_ETF_TRADE_QTY = int(os.getenv("HK_ETF_TRADE_QTY", "100"))
        cls.HK_ETF_STOP_LOSS_PCT = float(os.getenv("HK_ETF_STOP_LOSS_PCT", "5.0"))
        cls.HK_ETF_TAKE_PROFIT_PCT = float(os.getenv("HK_ETF_TAKE_PROFIT_PCT", "8.0"))
        cls.HK_ETF_STRATEGY = os.getenv("HK_ETF_STRATEGY", "all").lower()

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
