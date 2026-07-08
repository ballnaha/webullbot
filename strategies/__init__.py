from strategies.sma_crossover import SMACrossoverStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.hybrid_strategy import SmaRsiHybridStrategy

def get_strategy(strategy_name: str = "sma", **kwargs):
    """
    Factory function to initialize and return a trading strategy.
    """
    name = strategy_name.lower()
    if name == "sma":
        fast = int(kwargs.get("fast_period", 10))
        slow = int(kwargs.get("slow_period", 30))
        return SMACrossoverStrategy(fast_period=fast, slow_period=slow)
        
    elif name == "rsi":
        period = int(kwargs.get("period", 14))
        oversold = float(kwargs.get("oversold", 30.0))
        overbought = float(kwargs.get("overbought", 70.0))
        return RSIStrategy(period=period, oversold=oversold, overbought=overbought)
        
    elif name == "hybrid":
        fast = int(kwargs.get("fast_period", 10))
        slow = int(kwargs.get("slow_period", 30))
        period = int(kwargs.get("period", 14))
        oversold = float(kwargs.get("oversold", 40.0))
        overbought = float(kwargs.get("overbought", 60.0))
        return SmaRsiHybridStrategy(fast_period=fast, slow_period=slow, rsi_period=period, oversold=oversold, overbought=overbought)
        
    else:
        raise ValueError(f"Unsupported strategy name: {strategy_name}")
