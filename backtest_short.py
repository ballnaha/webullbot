import argparse
from pathlib import Path
import pandas as pd
from backtest_yfinance import DEFAULT_SYMBOLS, download_symbol
from strategies import get_strategy


def run_symbol(df, capital=10000.0, slip_bps=5.0, fee=0.0):
    strategy = get_strategy("short_regime", fast_period=20, slow_period=50, rsi_period=14, rsi_entry=55, rsi_cover=60)
    slip = slip_bps / 10000.0
    cash, qty, entry = capital, 0.0, 0.0
    curve, trades = [], []
    for i in range(55, len(df)):
        signal = strategy.generate_signal(df.iloc[:i])
        op, close = float(df.open.iloc[i]), float(df.close.iloc[i])
        if qty == 0 and signal == "SELL":
            entry = op * (1 - slip); qty = max(0, (cash - fee) / entry); cash += qty * entry - fee
        elif qty > 0 and signal == "BUY":
            exit_price = op * (1 + slip); pnl = qty * (entry - exit_price) - 2 * fee
            cash -= qty * exit_price + fee
            trades.append(pnl); qty = 0; entry = 0
        curve.append(cash - qty * close)
    if qty > 0:
        exit_price = float(df.close.iloc[-1]) * (1 + slip); trades.append(qty * (entry - exit_price) - 2 * fee); cash -= qty * exit_price + fee; curve.append(cash)
    v = pd.Series(curve); dd=(v/v.cummax()-1)*100
    wins=[x for x in trades if x>0]; losses=[x for x in trades if x<0]
    return {"return_pct":round((v.iloc[-1]/capital-1)*100,2),"max_drawdown_pct":round(dd.min(),2),"trades":len(trades),"win_rate_pct":round(len(wins)/len(trades)*100,2) if trades else 0,"profit_factor":round(sum(wins)/abs(sum(losses)),3) if losses else ("inf" if wins else 0)}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--period',default='5y'); p.add_argument('--symbols',default=','.join(DEFAULT_SYMBOLS)); p.add_argument('--out',default='backtest_results/short_regime'); a=p.parse_args(); rows=[]
    for symbol in [x.strip().upper() for x in a.symbols.split(',') if x.strip()]:
        df=download_symbol(symbol,a.period)
        if len(df)<100: rows.append({'symbol':symbol,'status':'NO_DATA','bars':len(df)}); continue
        m=run_symbol(df); m.update({'symbol':symbol,'status':'OK','bars':len(df),'period':a.period}); rows.append(m)
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); pd.DataFrame(rows).to_csv(out/'summary.csv',index=False); print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__': main()