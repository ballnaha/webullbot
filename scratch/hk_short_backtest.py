"""Out-of-sample backtest of HK bearish signals traded via inverse ETFs."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scratch.hk_strategy_backtest import FEE_RATE, SLIPPAGE, signal_series


PAIRS = {
    "0700.HK": "7500.HK", "9988.HK": "7500.HK", "2318.HK": "7500.HK",
    "0388.HK": "7500.HK", "1299.HK": "7500.HK", "0005.HK": "7500.HK",
    "0941.HK": "7500.HK", "3988.HK": "7500.HK",
    "1810.HK": "7552.HK", "3690.HK": "7552.HK", "9618.HK": "7552.HK",
    "1024.HK": "7552.HK", "9888.HK": "7552.HK", "2015.HK": "7552.HK",
    "1211.HK": "7552.HK",
}


def candidates():
    for fast, slow in [(5, 20), (10, 30), (20, 50), (50, 200)]:
        yield "sma", {"fast_period": fast, "slow_period": slow}
    for os_, ob in [(25, 65), (30, 70), (35, 65), (40, 60)]:
        yield "rsi", {"period": 14, "oversold": os_, "overbought": ob}
    for fast, slow, os_, ob in [(10, 30, 40, 60), (20, 30, 40, 60),
                                (20, 50, 35, 60), (20, 50, 40, 65)]:
        yield "hybrid", {"fast_period": fast, "slow_period": slow, "period": 14,
                         "oversold": os_, "overbought": ob}


def run_pair(stock, etf, sig, start, stop, take):
    idx = stock.index.intersection(etf.index)
    stock, etf, sig = stock.loc[idx], etf.loc[idx], sig.reindex(idx).fillna(0)
    cash, units, entry, entry_value = 1.0, 0.0, 0.0, 0.0
    curve, trades, wins = [], 0, 0
    for i in range(max(1, start), len(idx)):
        o, h, l, c = (float(etf.iloc[i][x]) for x in ("open", "high", "low", "close"))
        bearish_signal = int(sig.iloc[i - 1]) < 0
        bullish_signal = int(sig.iloc[i - 1]) > 0
        exit_px = None
        if units:
            if stop and l <= entry * (1 - stop):
                exit_px = min(o, entry * (1 - stop))
            elif take and h >= entry * (1 + take):
                exit_px = max(o, entry * (1 + take))
            elif bullish_signal:
                exit_px = o
        if exit_px is not None:
            proceeds = units * exit_px * (1 - SLIPPAGE) * (1 - FEE_RATE)
            wins += proceeds > entry_value
            cash, units, trades = proceeds, 0.0, trades + 1
        if not units and bearish_signal:
            entry = o * (1 + SLIPPAGE)
            entry_value = cash
            units = cash * (1 - FEE_RATE) / entry
            cash = 0.0
        curve.append(cash + units * c)
    if units:
        proceeds = units * float(etf.iloc[-1].close) * (1 - SLIPPAGE) * (1 - FEE_RATE)
        wins += proceeds > entry_value
        trades += 1
    eq = pd.Series(curve)
    years = max(len(eq) / 252, 1 / 252)
    cagr = eq.iloc[-1] ** (1 / years) - 1
    dd = (eq / eq.cummax() - 1).min()
    return cagr, dd, trades, wins / trades if trades else np.nan


def main():
    cache = Path("scratch/yf_cache")
    cache.mkdir(exist_ok=True)
    yf.set_tz_cache_location(str(cache.resolve()))
    symbols = sorted(set(PAIRS) | set(PAIRS.values()))
    raw = yf.download(symbols, period="5y", interval="1d", auto_adjust=True,
                      group_by="ticker", progress=False, threads=True)
    data = {s: raw[s].rename(columns=str.lower).dropna(subset=["open", "close"])
            [["open", "high", "low", "close", "volume"]] for s in symbols}
    rows = []
    for name, params in candidates():
        for sl in (0.03, 0.05, 0.08):
            for tp in (0.06, 0.10, 0.15):
                train, test = [], []
                for stock_symbol, etf_symbol in PAIRS.items():
                    stock, etf = data[stock_symbol], data[etf_symbol]
                    sig = signal_series(stock, name, params)
                    split_date = stock.index[int(len(stock) * .60)]
                    aligned = stock.index.intersection(etf.index)
                    split = int(aligned.searchsorted(split_date))
                    train.append(run_pair(stock.loc[:split_date], etf.loc[:split_date],
                                          sig.loc[:split_date], 0, sl, tp))
                    test.append(run_pair(stock, etf, sig, split, sl, tp))
                for segment, vals in (("train", train), ("test", test)):
                    a = np.asarray(vals, float)
                    rows.append({"strategy": name, "params": str(params), "sl": sl, "tp": tp,
                                 "segment": segment, "median_cagr": np.nanmedian(a[:, 0]),
                                 "mean_cagr": np.nanmean(a[:, 0]), "median_dd": np.nanmedian(a[:, 1]),
                                 "mean_trades": np.nanmean(a[:, 2]),
                                 "win_rate": np.nansum(a[:, 3] * a[:, 2]) / max(np.nansum(a[:, 2]), 1)})
    result = pd.DataFrame(rows)
    train = result[result.segment == "train"].copy()
    train["score"] = train.median_cagr / train.median_dd.abs().clip(lower=.02)
    train.loc[train.mean_trades < 3, "score"] = -np.inf
    chosen = train.sort_values("score", ascending=False).head(10)
    out = chosen.merge(result[result.segment == "test"],
                       on=["strategy", "params", "sl", "tp"], suffixes=("_train", "_test"))
    out.to_csv("scratch/hk_short_backtest_results.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
