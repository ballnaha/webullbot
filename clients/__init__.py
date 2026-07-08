from clients.local_paper import LocalPaperTradingClient
from clients.webull_unofficial import WebullUnofficialClient
from clients.webull_official import WebullOfficialClient

def get_client():
    """
    Factory function to initialize and return the correct trading client
    based on the configuration settings in config.py.
    """
    from config import Config
    
    mode = Config.TRADE_MODE
    
    if mode == "LOCAL_PAPER":
        return LocalPaperTradingClient(
            initial_cash=Config.SIMULATED_INITIAL_CASH,
            portfolio_file=Config.PORTFOLIO_FILE
        )
        
    elif mode == "WEBULL_PAPER":
        return WebullUnofficialClient(
            username=Config.WEBULL_USERNAME,
            password=Config.WEBULL_PASSWORD,
            is_paper=True,
            device_name=Config.WEBULL_DEVICE_NAME
        )
        
    elif mode == "WEBULL_LIVE":
        return WebullUnofficialClient(
            username=Config.WEBULL_USERNAME,
            password=Config.WEBULL_PASSWORD,
            trade_pin=Config.WEBULL_TRADE_PIN,
            is_paper=False,
            device_name=Config.WEBULL_DEVICE_NAME
        )
        
    elif mode == "WEBULL_OFFICIAL":
        return WebullOfficialClient(
            app_key=Config.WEBULL_APP_KEY,
            app_secret=Config.WEBULL_APP_SECRET
        )
        
    else:
        raise ValueError(f"Unsupported TRADE_MODE: {mode}")
