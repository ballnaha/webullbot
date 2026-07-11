"""Portfolio backtest for the project's low-priced HK universe and HKD 780 capital."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from config import Config

INITIAL_CASH=1000.0
MAX_ENTRY_PRICE=20.0
FEE,SLIP=.0012,.0005


def make_signals(df,name,p):
    c=df.close; buy=pd.Series(False,index=df.index);sell=buy.copy()
    if name in ('sma','hybrid'):
        f=c.rolling(p['fast']).mean();s=c.rolling(p['slow']).mean()
        cross_up=(f.shift(1)<=s.shift(1))&(f>s);cross_dn=(f.shift(1)>=s.shift(1))&(f<s)
    if name in ('rsi','hybrid'):
        d=c.diff();g=d.clip(lower=0).ewm(alpha=1/p.get('period',14),adjust=False).mean();l=(-d.clip(upper=0)).ewm(alpha=1/p.get('period',14),adjust=False).mean()
        r=100-100/(1+g/l.replace(0,1e-9));os,ob=p['os'],p['ob']
        up=(r.shift(1)<os)&(r>=os);dn=(r.shift(1)>ob)&(r<=ob)
    if name=='sma':buy,sell=cross_up,cross_dn
    elif name=='rsi':buy,sell=up,dn
    else:buy=(cross_up&(r<ob))|(up&(f>s));sell=cross_dn|dn
    strength=c.pct_change(20).fillna(-99)
    return buy.fillna(False),sell.fillna(False),strength


def qty_for(symbol,price,cash):
    lot=int(Config.HK_BOARD_LOTS.get(symbol,Config.HK_DEFAULT_BOARD_LOT))
    cap=int(Config.HK_MAX_QTY_PER_SLOT)
    max_qty=(cap//lot)*lot if cap>0 else 10**9
    affordable=int(cash/(price*(1+SLIP)*(1+FEE))//lot)*lot
    return max(0,min(max_qty,affordable))


def run(data,signals,start,end,sl,tp):
    dates=sorted(set().union(*(set(d.index) for d in data.values())));end=len(dates) if end is None else end
    cash=INITIAL_CASH;positions={};curve=[];trades=[]
    for di in range(start,end):
        date=dates[di]
        # Existing positions exit first, using only today's bar and yesterday's signal.
        for sym in list(positions):
            if date not in data[sym].index:continue
            bar=data[sym].loc[date];pos=positions[sym];out=None;reason=None
            if float(bar.low)<=pos['entry']*(1-sl):out=min(float(bar.open),pos['entry']*(1-sl));reason='SL'
            elif float(bar.high)>=pos['entry']*(1+tp):out=max(float(bar.open),pos['entry']*(1+tp));reason='TP'
            else:
                loc=data[sym].index.get_loc(date)
                if loc>0 and bool(signals[sym][1].iloc[loc-1]):out=float(bar.open);reason='SIGNAL'
            if out is not None:
                px=out*(1-SLIP);proceeds=pos['qty']*px*(1-FEE);cash+=proceeds
                trades.append({'symbol':sym,'entry_date':pos['date'],'exit_date':date,'pnl':proceeds-pos['cost'],'reason':reason})
                del positions[sym]
        # Rank all valid next-open entries by prior 20-day momentum.
        candidates=[]
        for sym,d in data.items():
            if sym in positions or date not in d.index:continue
            loc=d.index.get_loc(date)
            if loc<=0 or not bool(signals[sym][0].iloc[loc-1]):continue
            price=float(d.loc[date].open)
            if price<=MAX_ENTRY_PRICE:
                candidates.append((float(signals[sym][2].iloc[loc-1]),sym,price))
        for _,sym,price in sorted(candidates,reverse=True):
            qty=qty_for(sym,price,cash)
            if qty<=0:continue
            px=price*(1+SLIP);cost=qty*px*(1+FEE);cash-=cost
            positions[sym]={'qty':qty,'entry':px,'cost':cost,'date':date}
        value=cash
        for sym,pos in positions.items():
            hist=data[sym].loc[:date]
            value+=pos['qty']*float(hist.close.iloc[-1])
        curve.append(value/INITIAL_CASH)
    eq=pd.Series(curve);years=max(len(eq)/252,1/252);cagr=eq.iloc[-1]**(1/years)-1;dd=(eq/eq.cummax()-1).min()
    wins=sum(t['pnl']>0 for t in trades);return cagr,dd,len(trades),wins/len(trades) if trades else np.nan,eq.iloc[-1]-1,trades


def main():
    symbols=[s for s in Config.DEFAULT_SYMBOLS if s.endswith('.HK') and not s.startswith(('7','3'))]
    # Include all ordinary HK names from config; exclude known inverse/leveraged ETFs only.
    symbols=[s for s in Config.DEFAULT_SYMBOLS if s.endswith('.HK') and s not in {'7200.HK','7300.HK','7500.HK','7226.HK','7330.HK','7552.HK','7288.HK','7388.HK','7588.HK'}]
    cache=Path('scratch/yf_cache');cache.mkdir(exist_ok=True);yf.set_tz_cache_location(str(cache.resolve()))
    raw=yf.download(symbols,period='5y',interval='1d',auto_adjust=True,group_by='ticker',progress=False,threads=True)
    data={}
    for s in symbols:
        try:d=raw[s].rename(columns=str.lower).dropna(subset=['open','close'])[['open','high','low','close','volume']]
        except Exception:continue
        if len(d)>=500:data[s]=d
    all_dates=sorted(set().union(*(set(d.index) for d in data.values())));split=int(len(all_dates)*.6)
    configs=[('sma',{'fast':5,'slow':20}),('sma',{'fast':10,'slow':30}),('sma',{'fast':20,'slow':50}),
             ('rsi',{'period':14,'os':30,'ob':70}),('rsi',{'period':14,'os':35,'ob':65}),
             ('hybrid',{'fast':10,'slow':30,'period':14,'os':40,'ob':60}),('hybrid',{'fast':20,'slow':50,'period':14,'os':40,'ob':60})]
    rows=[];all_trades=[]
    for name,p in configs:
      sig={s:make_signals(d,name,p) for s,d in data.items()}
      for sl,tp in [(.03,.06),(.05,.10)]:
        tr=run(data,sig,0,split,sl,tp);te=run(data,sig,split,None,sl,tp)
        key=f'{name}:{p},sl{sl},tp{tp}'
        rows.append({'strategy':key,'train_cagr':tr[0],'train_dd':tr[1],'train_trades':tr[2],'test_cagr':te[0],'test_dd':te[1],'test_trades':te[2],'test_win_rate':te[3],'test_total':te[4]})
        for t in te[5]:t.update({'strategy':key});all_trades.append(t)
    result=pd.DataFrame(rows);result['score']=result.train_cagr+result.train_dd*.25;result.loc[result.train_trades<5,'score']=-np.inf
    result=result.sort_values('score',ascending=False);result.to_csv('scratch/hk_low_price_results.csv',index=False)
    pd.DataFrame(all_trades).to_csv('scratch/hk_low_price_trades.csv',index=False)
    print('symbols',len(data),'dates',len(all_dates),'split',all_dates[split]);print(result.to_string(index=False))
    if all_trades:print('\nMost traded\n',pd.DataFrame(all_trades).symbol.value_counts().head(15).to_string())

if __name__=='__main__':main()
