"""Yahoo Finance backtest for the project's long-only strategies.

Signals are evaluated using data through the previous completed bar and orders
are filled at the next bar open, so this intentionally avoids look-ahead bias.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf
from yfinance import cache

from config import Config
from strategies import get_strategy

DEFAULT_SYMBOLS = ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "META", "GOOGL", "NFLX", "AMD", "INTC"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest WebullBot strategies with Yahoo Finance data")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    parser.add_argument("--period", default="5y", help="Yahoo period, e.g. 2y, 5y, max")
    parser.add_argument("--strategy", default=Config.STRATEGY_US, choices=["sma", "rsi", "hybrid", "volume_ema", "regime_adaptive"])
    parser.add_argument("--capital", type=float, default=10000.0, help="Starting capital per symbol")
    parser.add_argument("--slippage-bps", type=float, default=Config.PAPER_SLIPPAGE_BPS)
    parser.add_argument("--fee", type=float, default=Config.PAPER_FEE_USD)
    parser.add_argument("--out", default="backtest_results")
    return parser.parse_args()


def download_symbol(symbol: str, period: str) -> pd.DataFrame:
    cache.set_cache_location("backtest_results/yf_cache")
    raw = yf.download(symbol, period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
    if raw is None or raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw = raw.rename(columns={c: str(c).lower() for c in raw.columns})
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(raw.columns):
        return pd.DataFrame()
    return raw.dropna(subset=["open", "high", "low", "close", "volume"])[["open", "high", "low", "close", "volume"]].copy()


def backtest_symbol(df: pd.DataFrame, strategy_name: str, capital: float, slippage_bps: float, fee: float, strategy_kwargs: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    kwargs = {"fast_period": 10, "slow_period": 30, "period": 14, "rsi_period": 14, "vol_period": 20, "vol_factor": 2.5}
    if strategy_kwargs:
        kwargs.update(strategy_kwargs)
    strategy = get_strategy(strategy_name, **kwargs)
    cash = float(capital)
    qty = 0.0
    entry_price = 0.0
    entry_date = None
    equity = []
    trades = []
    slip = slippage_bps / 10000.0
    warmup = 35

    for i in range(warmup, len(df)):
        date = df.index[i]
        open_price = float(df["open"].iloc[i])
        close_price = float(df["close"].iloc[i])
        history = df.iloc[:i]
        signal = strategy.generate_signal(history)

        if qty == 0 and signal == "BUY":
            fill = open_price * (1.0 + slip)
            qty = max(0.0, (cash - fee) / fill)
            if qty > 0:
                cash -= qty * fill + fee
                entry_price = fill
                entry_date = date
        elif qty > 0 and signal == "SELL":
            fill = open_price * (1.0 - slip)
            proceeds = qty * fill - fee
            pnl = proceeds - (qty * entry_price + fee)
            cash += proceeds
            trades.append({"entry": str(entry_date), "exit": str(date), "entry_price": entry_price, "exit_price": fill, "qty": qty, "pnl": pnl})
            qty = 0.0
            entry_price = 0.0
            entry_date = None

        equity.append({"date": str(date), "equity": cash + qty * close_price})

    if qty > 0:
        date = df.index[-1]
        fill = float(df["close"].iloc[-1]) * (1.0 - slip)
        proceeds = qty * fill - fee
        pnl = proceeds - (qty * entry_price + fee)
        cash += proceeds
        trades.append({"entry": str(entry_date), "exit": str(date), "entry_price": entry_price, "exit_price": fill, "qty": qty, "pnl": pnl})
        qty = 0.0
        equity.append({"date": str(date), "equity": cash})

    curve = pd.DataFrame(equity)
    if curve.empty:
        return {"return_pct": 0.0, "max_drawdown_pct": 0.0, "trades": 0, "win_rate_pct": 0.0, "profit_factor": 0.0}, trades
    values = curve["equity"]
    peak = values.cummax()
    drawdown = (values / peak - 1.0) * 100.0
    wins = [t["pnl"] for t in trades if t["pnl"] > 0]
    losses = [t["pnl"] for t in trades if t["pnl"] < 0]
    profit_factor = sum(wins) / abs(sum(losses)) if losses else (float("inf") if wins else 0.0)
    return {
        "return_pct": round((values.iloc[-1] / capital - 1.0) * 100.0, 2),
        "max_drawdown_pct": round(float(drawdown.min()), 2),
        "trades": len(trades),
        "win_rate_pct": round((len(wins) / len(trades)) * 100.0, 2) if trades else 0.0,
        "profit_factor": round(profit_factor, 3) if profit_factor != float("inf") else "inf",
        "final_equity": round(float(values.iloc[-1]), 2),
    }, trades


def main() -> None:
    args = parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    results = []
    all_trades = []
    for symbol in symbols:
        try:
            df = download_symbol(symbol, args.period)
            if len(df) < 40:
                results.append({"symbol": symbol, "status": "NO_DATA", "bars": len(df)})
                continue
            metrics, trades = backtest_symbol(df, args.strategy, args.capital, args.slippage_bps, args.fee)
            metrics["buy_hold_return_pct"] = round((float(df["close"].iloc[-1]) / float(df["close"].iloc[0]) - 1.0) * 100.0, 2)
            metrics.update({"symbol": symbol, "status": "OK", "bars": len(df), "period": args.period, "strategy": args.strategy})
            results.append(metrics)
            all_trades.extend([{**t, "symbol": symbol} for t in trades])
        except Exception as exc:
            results.append({"symbol": symbol, "status": "ERROR", "error": str(exc)})

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(out / "summary.csv", index=False)
    pd.DataFrame(all_trades).to_csv(out / "trades.csv", index=False)
    report = {"strategy": args.strategy, "period": args.period, "symbols": symbols, "slippage_bps": args.slippage_bps, "fee": args.fee, "results": results}
    (out / "report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(pd.DataFrame(results).to_string(index=False))
    print(f"\nSaved reports to {out.resolve()}")


if __name__ == "__main__":
    main()
