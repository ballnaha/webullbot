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
    # US order budget in USD (legacy name retained for UI/API compatibility).
    TRADE_QUANTITY = 100.0
    TRADE_QUANTITY_HK = 100
    HK_TRADE_BUDGET_HKD = 2000.0
    HK_ETF_BUDGET_HKD = 1000.0
    HK_DEFAULT_BOARD_LOT = 100
    HK_BOARD_LOTS = {
        # Verified examples from Webull's official Stock Trading API docs.
        "0700.HK": 100,
        "0005.HK": 400,
        "1299.HK": 200,
        "1810.HK": 200,
        "3690.HK": 100,
        "9618.HK": 50,
        "1211.HK": 500,
        "7500.HK": 100,
        "7552.HK": 100,
        "7300.HK": 100,
        "3033.HK": 200,
        "3067.HK": 100,
        # Low-priced board lots verified for 1000 HKD strategy.
        "0001.HK": 100, "0002.HK": 500, "0003.HK": 500, "0006.HK": 500,
        "0011.HK": 100, "0012.HK": 100, "0016.HK": 100, "0027.HK": 1000,
        "0066.HK": 100, "0101.HK": 500, "0175.HK": 1000, "0241.HK": 500,
        "0267.HK": 500, "0291.HK": 1000, "0322.HK": 1000, "0386.HK": 1000,
        "0388.HK": 100, "0669.HK": 500, "0688.HK": 1000, "0728.HK": 500,
        "0762.HK": 500, "0763.HK": 1000, "0823.HK": 500, "0857.HK": 1000,
        "0867.HK": 500, "0939.HK": 500, "0941.HK": 500, "0960.HK": 500,
        "0966.HK": 500, "0968.HK": 1000, "0981.HK": 500, "0992.HK": 1000,
        "1024.HK": 100, "1038.HK": 1000, "1044.HK": 1000, "1088.HK": 500,
        "1093.HK": 200, "1109.HK": 500, "1113.HK": 500, "1177.HK": 200,
        "1199.HK": 100, "1347.HK": 500, "1378.HK": 2000, "1398.HK": 1000,
        "1772.HK": 1000, "1818.HK": 500, "1876.HK": 100, "1898.HK": 1000,
        "1918.HK": 2000, "1928.HK": 1000, "2007.HK": 2000, "2015.HK": 100,
        "2020.HK": 500, "2269.HK": 500, "2318.HK": 500, "2319.HK": 1000,
        "2331.HK": 500, "2333.HK": 500, "2359.HK": 500, "2382.HK": 500,
        "2628.HK": 500, "2899.HK": 500, "3988.HK": 1000, "6618.HK": 100,
        "6862.HK": 100, "9626.HK": 100, "9696.HK": 100, "9866.HK": 100,
        "9868.HK": 100, "9888.HK": 100, "9988.HK": 100, "9999.HK": 100,
        "0883.HK": 1000,
    }
    HK_MAX_SLOTS = 1
    HK_MAX_PRICE_PER_SLOT = 8.0
    HK_MAX_QTY_PER_SLOT = 100
    HK_FILTER_PRICE_LIMIT = 8.0
    HK_FILTER_PRICE_OPERATOR = "le"
    INTERVAL = 60
    CANDLE_PERIOD = "d"
    STRATEGY_US = "sma"
    STRATEGY_HK = "rsi"
    HK_SMA_FAST_PERIOD = 20
    HK_SMA_SLOW_PERIOD = 50
    SIMULATED_INITIAL_CASH = 10000.0
    SIMULATED_INITIAL_CASH_HKD = 78000.0
    USD_HKD_RATE = 7.8
    PORTFOLIO_FILE = "local_portfolio.json"

    # ── HK Risk Management ──────────────────────────────────────────────────────
    # Stop Loss: ตัดขาดทุนเมื่อราคาร่วงเกิน % จากต้นทุน (0 = ปิดใช้งาน)
    HK_STOP_LOSS_PCT = 3.0
    # Take Profit: ทำกำไรเมื่อราคาขึ้นเกิน % จากต้นทุน (0 = ปิดใช้งาน)
    HK_TAKE_PROFIT_PCT = 6.0
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
    US_ALLOW_NAKED_INVERSE = False
    US_HEDGE_RATIO = 1.0
    US_STOP_LOSS_PCT = 5.0
    US_TAKE_PROFIT_PCT = 8.0
    US_TRAILING_STOP_PCT = 0.0
    US_MAX_HOLD_DAYS = 0
    US_DAILY_LOSS_LIMIT_USD = 0.0
    US_ETF_STOP_LOSS_PCT = 7.0
    US_ETF_TAKE_PROFIT_PCT = 10.0
    US_ETF_TRAILING_STOP_PCT = 0.0
    REGULAR_HOURS_ONLY = True
    US_MIN_ORDER_VALUE = 1.0
    PAPER_SLIPPAGE_BPS = 5.0
    PAPER_FEE_USD = 0.0
    PAPER_FEE_HK_RATE = 0.0012
    PAPER_STRICT_MARKET_RULES = True
    PAPER_US_FRACTIONAL_SYMBOLS = {
        "AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "META", "GOOGL", "GOOG",
        "NFLX", "AMD", "INTC", "PLTR", "AVGO", "QQQ", "SPY", "PYPL",
        "BABA", "ADBE", "CRM", "NKE", "DIS", "SMH", "SOXX", "ARKK",
        "IWM", "XLF", "XLE", "GDX", "DIA", "SQQQ", "SPXS", "SOXS",
    }
    
    # HK ETF Settings
    HK_ETF_TRADE_QTY = 100
    HK_ETF_STOP_LOSS_PCT = 8.0
    HK_ETF_TAKE_PROFIT_PCT = 15.0
    HK_ETF_STRATEGY = "trend_cash_3067"
    HK_LONG_ETF_SYMBOL = "3067.HK"
    HK_ETF_TREND_FAST = 20
    HK_ETF_TREND_SLOW = 50
    HK_ETF_MOMENTUM_PERIOD = 20
    HK_ETF_REBALANCE_BARS = 5
    HK_SHORT_BEARISH_THRESHOLD = 0.60
    HK_SHORT_EXIT_THRESHOLD = 0.30
    HK_ALLOW_NAKED_INVERSE = False
    HK_HEDGE_RATIO = 0.50
    
    # Inverse ETF hedging configurations
    ENABLE_INVERSE_ETF_HEDGING = False
    INVERSE_ETF_MAP = {
        "AAPL": "AAPD",        # 1x Short Apple
        "TSLA": "TSLQ",        # 2x Short Tesla
        "NVDA": "NVDS",        # 1.5x Short Nvidia
        "MSFT": "MSFD",        # 1.5x Short Microsoft
        "AMZN": "AMZD",        # 1x Short Amazon
        "GOOGL": "GGLS",       # 1x Short Google
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
        cls.TRADE_QUANTITY = float(os.getenv("TRADE_QUANTITY", "100.0"))
        cls.TRADE_QUANTITY_HK = int(os.getenv("TRADE_QUANTITY_HK", "100"))
        cls.HK_TRADE_BUDGET_HKD = float(os.getenv("HK_TRADE_BUDGET_HKD", "2000.0"))
        cls.HK_ETF_BUDGET_HKD = float(os.getenv("HK_ETF_BUDGET_HKD", "1000.0"))
        cls.HK_DEFAULT_BOARD_LOT = int(os.getenv("HK_DEFAULT_BOARD_LOT", "100"))
        cls.HK_MAX_SLOTS = int(os.getenv("HK_MAX_SLOTS", "1"))
        cls.HK_MAX_PRICE_PER_SLOT = float(os.getenv("HK_MAX_PRICE_PER_SLOT", "999999.0"))
        cls.HK_MAX_QTY_PER_SLOT = int(os.getenv("HK_MAX_QTY_PER_SLOT", "100"))
        cls.HK_FILTER_PRICE_LIMIT = float(os.getenv("HK_FILTER_PRICE_LIMIT", "20.0"))
        cls.HK_FILTER_PRICE_OPERATOR = os.getenv("HK_FILTER_PRICE_OPERATOR", "le").lower()
        cls.INTERVAL = int(os.getenv("INTERVAL", "60"))
        cls.CANDLE_PERIOD = os.getenv("CANDLE_PERIOD", "d").lower()
        cls.STRATEGY_US = os.getenv("STRATEGY_US", "sma").lower()
        cls.STRATEGY_HK = os.getenv("STRATEGY_HK", "sma").lower()
        cls.HK_SMA_FAST_PERIOD = int(os.getenv("HK_SMA_FAST_PERIOD", "20"))
        cls.HK_SMA_SLOW_PERIOD = int(os.getenv("HK_SMA_SLOW_PERIOD", "50"))
        cls.USD_HKD_RATE = float(os.getenv("USD_HKD_RATE", "7.8"))
        hkd_raw = os.getenv("SIMULATED_INITIAL_CASH_HKD", "").strip()
        usd_raw = os.getenv("SIMULATED_INITIAL_CASH", "").strip()
        if hkd_raw:
            cls.SIMULATED_INITIAL_CASH_HKD = float(hkd_raw)
        elif usd_raw:
            cls.SIMULATED_INITIAL_CASH_HKD = float(usd_raw) * cls.USD_HKD_RATE
        else:
            cls.SIMULATED_INITIAL_CASH_HKD = 78000.0
        # One shared cash pool: HKD is canonical and USD is always its conversion.
        cls.SIMULATED_INITIAL_CASH = cls.SIMULATED_INITIAL_CASH_HKD / cls.USD_HKD_RATE
        cls.ENABLE_INVERSE_ETF_HEDGING = os.getenv("ENABLE_INVERSE_ETF_HEDGING", "FALSE").upper() == "TRUE"
        # HK Risk Management
        cls.HK_STOP_LOSS_PCT = float(os.getenv("HK_STOP_LOSS_PCT", "6.0"))
        cls.HK_TAKE_PROFIT_PCT = float(os.getenv("HK_TAKE_PROFIT_PCT", "12.0"))
        cls.HK_TRAILING_STOP_PCT = float(os.getenv("HK_TRAILING_STOP_PCT", "0.0"))
        cls.HK_MAX_HOLD_DAYS = int(os.getenv("HK_MAX_HOLD_DAYS", "0"))
        cls.HK_DAILY_LOSS_LIMIT_HKD = float(os.getenv("HK_DAILY_LOSS_LIMIT_HKD", "0.0"))
        cls.HK_AUTO_LONG = os.getenv("HK_AUTO_LONG", "TRUE").upper() == "TRUE"
        cls.US_AUTO_LONG = os.getenv("US_AUTO_LONG", "TRUE").upper() == "TRUE"
        cls.US_ENABLE_INVERSE_ETF_HEDGING = os.getenv("US_ENABLE_INVERSE_ETF_HEDGING", "TRUE").upper() == "TRUE"
        cls.US_ETF_BUDGET = float(os.getenv("US_ETF_BUDGET", "300.0"))
        cls.US_ETF_STRATEGY = os.getenv("US_ETF_STRATEGY", "standard").lower()
        cls.US_ALLOW_NAKED_INVERSE = os.getenv("US_ALLOW_NAKED_INVERSE", "FALSE").upper() == "TRUE"
        cls.US_HEDGE_RATIO = float(os.getenv("US_HEDGE_RATIO", "1.0"))
        cls.US_STOP_LOSS_PCT = float(os.getenv("US_STOP_LOSS_PCT", "5.0"))
        cls.US_TAKE_PROFIT_PCT = float(os.getenv("US_TAKE_PROFIT_PCT", "8.0"))
        cls.US_TRAILING_STOP_PCT = float(os.getenv("US_TRAILING_STOP_PCT", "0.0"))
        cls.US_MAX_HOLD_DAYS = int(os.getenv("US_MAX_HOLD_DAYS", "0"))
        cls.US_DAILY_LOSS_LIMIT_USD = float(os.getenv("US_DAILY_LOSS_LIMIT_USD", "0.0"))
        cls.US_ETF_STOP_LOSS_PCT = float(os.getenv("US_ETF_STOP_LOSS_PCT", "7.0"))
        cls.US_ETF_TAKE_PROFIT_PCT = float(os.getenv("US_ETF_TAKE_PROFIT_PCT", "10.0"))
        cls.US_ETF_TRAILING_STOP_PCT = float(os.getenv("US_ETF_TRAILING_STOP_PCT", "0.0"))
        cls.REGULAR_HOURS_ONLY = os.getenv("REGULAR_HOURS_ONLY", "TRUE").upper() == "TRUE"
        cls.US_MIN_ORDER_VALUE = float(os.getenv("US_MIN_ORDER_VALUE", "1.0"))
        cls.PAPER_SLIPPAGE_BPS = float(os.getenv("PAPER_SLIPPAGE_BPS", "5.0"))
        cls.PAPER_FEE_USD = float(os.getenv("PAPER_FEE_USD", "0.0"))
        cls.PAPER_FEE_HK_RATE = float(os.getenv("PAPER_FEE_HK_RATE", "0.0012"))
        cls.PAPER_STRICT_MARKET_RULES = os.getenv("PAPER_STRICT_MARKET_RULES", "TRUE").upper() == "TRUE"
        cls.ENABLE_INVERSE_ETF_HEDGING = os.getenv("ENABLE_INVERSE_ETF_HEDGING", "FALSE").upper() == "TRUE"
        # HK ETF Settings
        cls.HK_ETF_TRADE_QTY = int(os.getenv("HK_ETF_TRADE_QTY", "100"))
        cls.HK_ETF_STOP_LOSS_PCT = float(os.getenv("HK_ETF_STOP_LOSS_PCT", "8.0"))
        cls.HK_ETF_TAKE_PROFIT_PCT = float(os.getenv("HK_ETF_TAKE_PROFIT_PCT", "15.0"))
        cls.HK_ETF_STRATEGY = os.getenv("HK_ETF_STRATEGY", "trend_cash_3067").lower()
        cls.HK_LONG_ETF_SYMBOL = os.getenv("HK_LONG_ETF_SYMBOL", "3067.HK").upper()
        cls.HK_ETF_TREND_FAST = int(os.getenv("HK_ETF_TREND_FAST", "20"))
        cls.HK_ETF_TREND_SLOW = int(os.getenv("HK_ETF_TREND_SLOW", "50"))
        cls.HK_ETF_MOMENTUM_PERIOD = int(os.getenv("HK_ETF_MOMENTUM_PERIOD", "20"))
        cls.HK_ETF_REBALANCE_BARS = int(os.getenv("HK_ETF_REBALANCE_BARS", "5"))
        cls.HK_SHORT_BEARISH_THRESHOLD = float(os.getenv("HK_SHORT_BEARISH_THRESHOLD", "0.60"))
        cls.HK_SHORT_EXIT_THRESHOLD = float(os.getenv("HK_SHORT_EXIT_THRESHOLD", "0.30"))
        cls.HK_ALLOW_NAKED_INVERSE = os.getenv("HK_ALLOW_NAKED_INVERSE", "FALSE").upper() == "TRUE"
        cls.HK_HEDGE_RATIO = float(os.getenv("HK_HEDGE_RATIO", "0.50"))

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
