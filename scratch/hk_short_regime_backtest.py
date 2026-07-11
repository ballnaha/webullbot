"""Walk-forward HK inverse ETF backtest driven by index regime/breakdown signals."""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import yfinance as yf

# Yahoo exposes insufficient history for HSTECH.HK, so 3033.HK (a long
# Hang Seng TECH tracker) is the executable historical proxy for that index.
PAIRS = {"^HSI": "7500.HK", "3033.HK": "7552.HK"}
FEE, SLIPPAGE = 0.0012, 0.0005


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df.high, df.low, df.close
    up, down = high.diff(), -low.diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    tr = pd.concat([(high-low), (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan)
    dx = 100 * (plus_di-minus_di).abs() / (plus_di+minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1/period, adjust=False).mean()


def signals(index_df, fast, slow, regime, breakdown, adx_min):
    c = index_df.close
    bearish = (c < c.rolling(regime).mean()) & (c.rolling(fast).mean() < c.rolling(slow).mean())
    breaking = c < index_df.low.shift(1).rolling(breakdown).min()
    strength = adx(index_df) >= adx_min
    enter = bearish & breaking & strength
    recover = (c > c.rolling(fast).mean()) | ~bearish
    return enter.fillna(False), recover.fillna(False)


def run(index_df, etf_df, enter, recover, start, sl, tp, max_hold):
    idx = index_df.index.intersection(etf_df.index)
    etf, enter, recover = etf_df.loc[idx], enter.reindex(idx).fillna(False), recover.reindex(idx).fillna(False)
    cash, units, entry_px, held, entry_value = 1.0, 0.0, 0.0, 0, 0.0
    curve, trades, wins = [], 0, 0
    for i in range(max(1, start), len(idx)):
        o, h, l, c = (float(etf.iloc[i][x]) for x in ("open", "high", "low", "close"))
        exit_px = None
        if units:
            held += 1
            # Conservative ordering if both barriers are touched in one bar.
            if l <= entry_px * (1-sl): exit_px = min(o, entry_px*(1-sl))
            elif h >= entry_px * (1+tp): exit_px = max(o, entry_px*(1+tp))
            elif bool(recover.iloc[i-1]) or held >= max_hold: exit_px = o
        if exit_px is not None:
            proceeds = units * exit_px * (1-SLIPPAGE) * (1-FEE)
            wins += proceeds > entry_value
            cash, units, trades = proceeds, 0.0, trades + 1
        if not units and bool(enter.iloc[i-1]):
            entry_px = o * (1+SLIPPAGE); entry_value = cash
            units = cash * (1-FEE) / entry_px; cash, held = 0.0, 0
        curve.append(cash + units*c)
    if units:
        proceeds = units * float(etf.iloc[-1].close) * (1-SLIPPAGE) * (1-FEE)
        wins += proceeds > entry_value; trades += 1
    eq = pd.Series(curve)
    years = max(len(eq)/252, 1/252)
    cagr = eq.iloc[-1]**(1/years)-1
    dd = (eq/eq.cummax()-1).min()
    daily = eq.pct_change().dropna()
    sharpe = np.sqrt(252)*daily.mean()/daily.std() if daily.std() > 0 else 0.0
    return cagr, dd, sharpe, trades, wins/trades if trades else np.nan


def main():
    cache = Path("scratch/yf_cache"); cache.mkdir(exist_ok=True)
    yf.set_tz_cache_location(str(cache.resolve()))
    symbols = list(PAIRS) + list(PAIRS.values())
    raw = yf.download(symbols, period="max", interval="1d", auto_adjust=True,
                      group_by="ticker", progress=False, threads=True)
    data = {}
    for s in symbols:
        d = raw[s].rename(columns=str.lower).dropna(subset=["open", "close"])
        data[s] = d[["open", "high", "low", "close", "volume"]]
        print(s, len(d), d.index.min(), d.index.max())
    configs = itertools.product(
        [(10,30), (20,50)], [100,200], [10,20], [15,20,25],
        [.03,.05], [.06,.10], [3,5,10]
    )
    rows = []
    for (fast,slow), regime, breakdown, adx_min, sl, tp, max_hold in configs:
        metrics = {"train": [], "test": []}
        for index_symbol, etf_symbol in PAIRS.items():
            ix, etf = data[index_symbol], data[etf_symbol]
            common = ix.index.intersection(etf.index)
            # ETF inception determines the usable sample; 60/40 chronological split.
            split = int(len(common)*.60)
            enter, recover = signals(ix, fast, slow, regime, breakdown, adx_min)
            metrics["train"].append(run(ix.loc[:common[split]], etf.loc[:common[split]], enter, recover, 0, sl, tp, max_hold))
            metrics["test"].append(run(ix, etf, enter, recover, split, sl, tp, max_hold))
        for segment, vals in metrics.items():
            a = np.asarray(vals, float)
            rows.append({"fast":fast,"slow":slow,"regime":regime,"breakdown":breakdown,
                         "adx":adx_min,"sl":sl,"tp":tp,"max_hold":max_hold,"segment":segment,
                         "mean_cagr":np.nanmean(a[:,0]),"worst_cagr":np.nanmin(a[:,0]),
                         "mean_dd":np.nanmean(a[:,1]),"mean_sharpe":np.nanmean(a[:,2]),
                         "trades":np.nansum(a[:,3]),"win_rate":np.nansum(a[:,4]*a[:,3])/max(np.nansum(a[:,3]),1)})
    result = pd.DataFrame(rows)
    keys = ["fast","slow","regime","breakdown","adx","sl","tp","max_hold"]
    train = result[result.segment=="train"].copy()
    train["score"] = train.mean_sharpe + train.mean_cagr - train.mean_dd.abs()*.25
    train.loc[train.trades < 8, "score"] = -np.inf
    selected = train.sort_values("score", ascending=False).head(15)
    out = selected.merge(result[result.segment=="test"], on=keys, suffixes=("_train","_test"))
    out.to_csv("scratch/hk_short_regime_results.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__": main()
