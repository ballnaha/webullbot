"""Walk-forward backtest for the Hong Kong strategies shipped with this project.

Signals use data through day T and execute at day T+1 open.  The script downloads
adjusted daily OHLCV data, selects parameters on the first 60% of observations,
and reports untouched out-of-sample performance on the remaining 40%.
"""
from __future__ import annotations

import itertools
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


SYMBOLS = [
    "0700.HK", "9988.HK", "1810.HK", "1211.HK", "3690.HK",
    "9618.HK", "0981.HK", "2318.HK", "0939.HK", "1398.HK",
    "3988.HK", "1024.HK", "9888.HK", "2015.HK", "9868.HK",
    "2269.HK", "2382.HK", "0388.HK", "1299.HK", "0005.HK",
]
# Approximation: stamp duty + exchange/levies + broker friction, each side.
FEE_RATE = 0.0012
SLIPPAGE = 0.0005


def candidates():
    for fast, slow in [(5, 20), (10, 30), (20, 50), (50, 200)]:
        yield "sma", {"fast_period": fast, "slow_period": slow}, 0, 0
    for os_, ob in [(25, 65), (30, 70), (35, 65), (40, 60)]:
        yield "rsi", {"period": 14, "oversold": os_, "overbought": ob}, 0, 0
    for fast, slow, os_, ob in itertools.product(
        [10, 20], [30, 50], [35, 40], [60, 65]
    ):
        yield "hybrid", {"fast_period": fast, "slow_period": slow,
                         "period": 14, "oversold": os_, "overbought": ob}, 0, 0
    for fast, slow, factor in itertools.product([5, 9], [21, 30], [1.2, 1.5, 2.0, 2.5]):
        yield "volume_ema", {"fast_period": fast, "slow_period": slow,
                             "vol_period": 20, "vol_factor": factor}, 0, 0
    # The live bot applies these exits independently of the signal strategy.
    for fast, slow, stop, take in itertools.product([5, 10, 20], [30, 50], [0.03, 0.05], [0.06, 0.10]):
        if fast < slow:
            yield "sma", {"fast_period": fast, "slow_period": slow}, stop, take


def signal_series(df: pd.DataFrame, name: str, params: dict) -> pd.Series:
    close = df.close
    out = pd.Series(0, index=df.index, dtype=np.int8)
    if name in ("sma", "hybrid"):
        fast = close.rolling(params["fast_period"]).mean()
        slow = close.rolling(params["slow_period"]).mean()
        golden = (fast.shift(1) <= slow.shift(1)) & (fast > slow)
        death = (fast.shift(1) >= slow.shift(1)) & (fast < slow)
    if name in ("rsi", "hybrid"):
        period = params.get("period", 14)
        delta = close.diff()
        gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
        rs = gain.ewm(alpha=1 / period, adjust=False).mean() / loss.ewm(alpha=1 / period, adjust=False).mean().replace(0, 1e-9)
        rsi = 100 - 100 / (1 + rs)
        os_, ob = params["oversold"], params["overbought"]
        exit_os = (rsi.shift(1) < os_) & (rsi >= os_)
        exit_ob = (rsi.shift(1) > ob) & (rsi <= ob)
    if name == "sma":
        buy, sell = golden, death
    elif name == "rsi":
        buy, sell = exit_os, exit_ob
    elif name == "hybrid":
        buy = (golden & (rsi < ob)) | (exit_os & (fast > slow))
        sell = death | exit_ob
    else:
        fast = close.ewm(span=params["fast_period"], adjust=False).mean()
        slow = close.ewm(span=params["slow_period"], adjust=False).mean()
        golden = (fast.shift(1) <= slow.shift(1)) & (fast > slow)
        death = (fast.shift(1) >= slow.shift(1)) & (fast < slow)
        vol_sma = df.volume.rolling(params["vol_period"]).mean()
        buy = golden & (df.volume > vol_sma * params["vol_factor"])
        sell = death | (close < slow)
    out.loc[buy.fillna(False)] = 1
    out.loc[sell.fillna(False)] = -1
    return out


def run_one(df: pd.DataFrame, sig: pd.Series, start: int, stop: float, take: float):
    cash, shares, entry = 1.0, 0.0, 0.0
    equity, trades, wins = [], 0, 0
    entry_value = 0.0
    for i in range(max(1, start), len(df)):
        o, h, l, c = (float(df.iloc[i][x]) for x in ("open", "high", "low", "close"))
        prev_sig = int(sig.iloc[i - 1])
        exit_px = None
        if shares:
            # Conservative convention when both barriers occur in one daily bar.
            if stop and l <= entry * (1 - stop):
                exit_px = min(o, entry * (1 - stop))
            elif take and h >= entry * (1 + take):
                exit_px = max(o, entry * (1 + take))
            elif prev_sig < 0:
                exit_px = o
        if exit_px is not None:
            proceeds = shares * exit_px * (1 - SLIPPAGE) * (1 - FEE_RATE)
            wins += proceeds > entry_value
            cash, shares, trades = proceeds, 0.0, trades + 1
        if not shares and prev_sig > 0:
            px = o * (1 + SLIPPAGE)
            entry_value = cash
            shares = cash * (1 - FEE_RATE) / px
            cash, entry = 0.0, px
        equity.append(cash + shares * c)
    if shares:
        proceeds = shares * float(df.iloc[-1].close) * (1 - SLIPPAGE) * (1 - FEE_RATE)
        wins += proceeds > entry_value
        trades += 1
    eq = pd.Series(equity)
    total = float(eq.iloc[-1] - 1) if len(eq) else 0.0
    dd = float((eq / eq.cummax() - 1).min()) if len(eq) else 0.0
    years = max(len(eq) / 252, 1 / 252)
    cagr = float(eq.iloc[-1] ** (1 / years) - 1) if len(eq) else 0.0
    return total, cagr, dd, trades, wins / trades if trades else np.nan


def main():
    cache = Path("scratch/yf_cache")
    cache.mkdir(exist_ok=True)
    yf.set_tz_cache_location(str(cache.resolve()))
    raw = yf.download(SYMBOLS, period="5y", interval="1d", auto_adjust=True,
                      group_by="ticker", progress=False, threads=True)
    data = {}
    for symbol in SYMBOLS:
        d = raw[symbol].rename(columns=str.lower).dropna(subset=["open", "close"])
        if len(d) >= 750:
            data[symbol] = d[["open", "high", "low", "close", "volume"]]
    print(f"Loaded {len(data)}/{len(SYMBOLS)} symbols")

    rows = []
    for name, params, sl, tp in candidates():
        train, test = [], []
        for symbol, d in data.items():
            sig = signal_series(d, name, params)
            split = int(len(d) * 0.60)
            train.append(run_one(d.iloc[:split], sig.iloc[:split], 0, sl, tp))
            # Retain earlier bars for indicator warm-up, but equity starts at split.
            test.append(run_one(d, sig, split, sl, tp))
        for segment, vals in (("train", train), ("test", test)):
            a = np.asarray(vals, dtype=float)
            rows.append({"strategy": name, "params": str(params), "sl": sl, "tp": tp,
                         "segment": segment, "median_total": np.nanmedian(a[:, 0]),
                         "median_cagr": np.nanmedian(a[:, 1]), "median_dd": np.nanmedian(a[:, 2]),
                         "mean_cagr": np.nanmean(a[:, 1]), "mean_trades": np.nanmean(a[:, 3]),
                         "win_rate": np.nansum(a[:, 4] * a[:, 3]) / max(np.nansum(a[:, 3]), 1)})
    result = pd.DataFrame(rows)
    train = result[result.segment == "train"].copy()
    # Reward return and penalize drawdown; require enough activity to be meaningful.
    train["score"] = train.median_cagr / train.median_dd.abs().clip(lower=.02)
    train.loc[train.mean_trades < 2, "score"] = -np.inf
    chosen = train.sort_values("score", ascending=False).head(10)
    joined = chosen.merge(result[result.segment == "test"], on=["strategy", "params", "sl", "tp"], suffixes=("_train", "_test"))
    cols = ["strategy", "params", "sl", "tp", "median_cagr_train", "median_dd_train",
            "median_cagr_test", "mean_cagr_test", "median_dd_test", "mean_trades_test", "win_rate_test"]
    joined[cols].to_csv("scratch/hk_backtest_results.csv", index=False)
    print(joined[cols].to_string(index=False))


if __name__ == "__main__":
    main()
