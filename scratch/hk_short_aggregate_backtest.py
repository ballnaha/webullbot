"""Walk-forward backtest for aggregate HK inverse-ETF signals."""
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

GROUPS = {
    "7500.HK": ["0700.HK", "9988.HK", "2318.HK", "0388.HK", "1299.HK", "0005.HK", "0941.HK", "3988.HK"],
    "7552.HK": ["1810.HK", "3690.HK", "9618.HK", "1024.HK", "9888.HK", "2015.HK", "1211.HK"],
}
FEE, SLIPPAGE = .0012, .0005


def run(etf, ratio, start, entry_threshold, exit_threshold, sl, tp):
    idx = etf.index.intersection(ratio.index)
    etf, ratio = etf.loc[idx], ratio.loc[idx]
    cash, units, entry = 1.0, 0.0, 0.0
    curve, trades, wins, entry_value = [], 0, 0, 0.0
    for i in range(max(1, start), len(idx)):
        o, h, l, c = (float(etf.iloc[i][x]) for x in ("open", "high", "low", "close"))
        exit_px = None
        if units:
            if l <= entry * (1 - sl): exit_px = min(o, entry * (1 - sl))
            elif h >= entry * (1 + tp): exit_px = max(o, entry * (1 + tp))
            elif ratio.iloc[i - 1] <= exit_threshold: exit_px = o
        if exit_px is not None:
            proceeds = units * exit_px * (1 - SLIPPAGE) * (1 - FEE)
            wins += proceeds > entry_value
            cash, units, trades = proceeds, 0, trades + 1
        if not units and ratio.iloc[i - 1] >= entry_threshold:
            entry = o * (1 + SLIPPAGE); entry_value = cash
            units = cash * (1 - FEE) / entry; cash = 0
        curve.append(cash + units * c)
    eq = pd.Series(curve)
    years = max(len(eq) / 252, 1 / 252)
    return eq.iloc[-1] ** (1 / years) - 1, (eq / eq.cummax() - 1).min(), trades, wins / trades if trades else np.nan


def main():
    cache = Path("scratch/yf_cache"); cache.mkdir(exist_ok=True)
    yf.set_tz_cache_location(str(cache.resolve()))
    symbols = sorted(set(GROUPS) | {s for group in GROUPS.values() for s in group})
    raw = yf.download(symbols, period="5y", interval="1d", auto_adjust=True, group_by="ticker", progress=False, threads=True)
    data = {s: raw[s].rename(columns=str.lower).dropna(subset=["open", "close"])[["open", "high", "low", "close", "volume"]] for s in symbols}
    rows = []
    for fast, slow in [(5, 20), (10, 30), (20, 50), (50, 200)]:
      ratios = {}
      for etf, stocks in GROUPS.items():
        states = [(data[s].close.rolling(fast).mean() < data[s].close.rolling(slow).mean()).rename(s) for s in stocks]
        ratios[etf] = pd.concat(states, axis=1).mean(axis=1)
      for enter in (.5, .6, .7):
       for leave in (.3, .4, .5):
        if leave >= enter: continue
        for sl, tp in [(.05, .10), (.08, .15)]:
         vals = {"train": [], "test": []}
         for etf in GROUPS:
            d, ratio = data[etf], ratios[etf]
            idx = d.index.intersection(ratio.index); split = int(len(idx) * .6)
            vals["train"].append(run(d.loc[:idx[split]], ratio.loc[:idx[split]], 0, enter, leave, sl, tp))
            vals["test"].append(run(d, ratio, split, enter, leave, sl, tp))
         for segment, metrics in vals.items():
            a = np.asarray(metrics, float)
            rows.append({"fast": fast, "slow": slow, "enter": enter, "exit": leave, "sl": sl, "tp": tp, "segment": segment,
                         "mean_cagr": np.nanmean(a[:, 0]), "worst_cagr": np.nanmin(a[:, 0]), "mean_dd": np.nanmean(a[:, 1]), "trades": np.nanmean(a[:, 2])})
    result = pd.DataFrame(rows); train = result[result.segment == "train"].copy()
    train["score"] = train.mean_cagr / train.mean_dd.abs().clip(lower=.02)
    chosen = train.sort_values("score", ascending=False).head(10)
    out = chosen.merge(result[result.segment == "test"], on=["fast", "slow", "enter", "exit", "sl", "tp"], suffixes=("_train", "_test"))
    out.to_csv("scratch/hk_short_aggregate_results.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__": main()
