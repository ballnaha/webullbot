"""Walk-forward parameter search for the yfinance backtester."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from backtest_yfinance import DEFAULT_SYMBOLS, download_symbol, backtest_symbol

SYMBOLS = DEFAULT_SYMBOLS
CAPITAL = 10000.0
SLIP = 5.0
FEE = 0.0

CANDIDATES = []
for fast, slow in [(5, 20), (10, 30), (10, 50), (20, 50), (20, 100)]:
    CANDIDATES.append(("sma", {"fast_period": fast, "slow_period": slow}, f"SMA {fast}/{slow}"))
for period, oversold, overbought in [(14, 30.0, 70.0), (14, 35.0, 65.0), (21, 30.0, 70.0), (21, 35.0, 65.0)]:
    CANDIDATES.append(("rsi", {"period": period, "oversold": oversold, "overbought": overbought}, f"RSI {period}/{oversold:.0f}/{overbought:.0f}"))
for fast, slow, period, oversold, overbought in [(10, 30, 14, 40.0, 60.0), (10, 30, 14, 30.0, 70.0), (20, 50, 14, 40.0, 60.0), (5, 20, 14, 40.0, 60.0)]:
    CANDIDATES.append(("hybrid", {"fast_period": fast, "slow_period": slow, "rsi_period": period, "oversold": oversold, "overbought": overbought}, f"Hybrid {fast}/{slow} RSI {oversold:.0f}/{overbought:.0f}"))
CANDIDATES.extend([
    ("regime_adaptive", {"fast_period": 20, "slow_period": 50, "rsi_period": 14, "rsi_entry": 45.0, "rsi_exit": 40.0, "rsi_ceiling": 68.0}, "Regime Adaptive 20/50"),
    ("regime_adaptive", {"fast_period": 10, "slow_period": 30, "rsi_period": 14, "rsi_entry": 45.0, "rsi_exit": 40.0, "rsi_ceiling": 68.0}, "Regime Adaptive 10/30"),
])


def run() -> None:
    datasets = {}
    for symbol in SYMBOLS:
        df = download_symbol(symbol, "5y")
        if len(df) >= 100:
            split = int(len(df) * 0.7)
            datasets[symbol] = (df.iloc[:split].copy(), df.iloc[split:].copy())
    rows = []
    for name, kwargs, label in CANDIDATES:
        train_metrics = []
        test_metrics = []
        for symbol, (train, test) in datasets.items():
            train_result, _ = backtest_symbol(train, name, CAPITAL, SLIP, FEE, kwargs)
            test_result, _ = backtest_symbol(test, name, CAPITAL, SLIP, FEE, kwargs)
            train_metrics.append(train_result)
            test_metrics.append(test_result)
        if not train_metrics:
            continue
        train_returns = [x["return_pct"] for x in train_metrics]
        test_returns = [x["return_pct"] for x in test_metrics]
        train_dd = [x["max_drawdown_pct"] for x in train_metrics]
        test_dd = [x["max_drawdown_pct"] for x in test_metrics]
        rows.append({
            "label": label, "strategy": name, "params": kwargs,
            "train_mean_return_pct": round(sum(train_returns)/len(train_returns), 2),
            "train_mean_drawdown_pct": round(sum(train_dd)/len(train_dd), 2),
            "test_mean_return_pct": round(sum(test_returns)/len(test_returns), 2),
            "test_median_return_pct": round(float(pd.Series(test_returns).median()), 2),
            "test_mean_drawdown_pct": round(sum(test_dd)/len(test_dd), 2),
            "test_profitable_symbols": int(sum(x > 0 for x in test_returns)),
            "test_symbols": len(test_returns),
        })
    # Select only by train score, then inspect test; this prevents test leakage.
    for row in rows:
        row["train_score"] = row["train_mean_return_pct"] + row["train_mean_drawdown_pct"]
    rows.sort(key=lambda x: x["train_score"], reverse=True)
    out = Path("backtest_results/optimization")
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).drop(columns=["params"]).to_csv(out / "optimization.csv", index=False)
    (out / "optimization.json").write_text(json.dumps(rows, indent=2, default=lambda x: int(x) if hasattr(x, "item") else x), encoding="utf-8")
    print(pd.DataFrame(rows).drop(columns=["params"]).head(10).to_string(index=False))
    if rows:
        print("\nSelected by train only:", rows[0]["label"])
        print("Out-of-sample result:", rows[0]["test_mean_return_pct"], "% mean return;", rows[0]["test_profitable_symbols"], "/", rows[0]["test_symbols"], "profitable")


if __name__ == "__main__":
    run()