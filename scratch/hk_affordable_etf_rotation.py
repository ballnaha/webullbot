"""Realistic 1000 HKD trend/rotation backtest for affordable long HK ETFs."""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import yfinance as yf

LOTS={"3033.HK":200,"3067.HK":100}
INITIAL=1000.;FEE=.0012;SLIP=.0005


def targets(data,fast,slow,mom,rebalance,mode):
    idx=data["3033.HK"].index.union(data["3067.HK"].index).sort_values()
    score={};trend={}
    for s,d in data.items():
        c=d.close.reindex(idx)
        score[s]=c.pct_change(mom)
        trend[s]=c.rolling(fast).mean()>c.rolling(slow).mean()
    out=pd.Series("CASH",index=idx,dtype=object);current="CASH"
    for i in range(len(idx)):
        if i%rebalance==0:
            candidates=[s for s in LOTS if bool(trend[s].iloc[i]) and pd.notna(score[s].iloc[i]) and score[s].iloc[i]>0]
            if candidates:
                current=max(candidates,key=lambda s:float(score[s].iloc[i])) if mode=="rotation" else "3067.HK"
            else:current="CASH"
        out.iloc[i]=current
    return out.shift(1).fillna("CASH")


def run(data,target,start):
    idx=target.index;cash=INITIAL;symbol=None;qty=0;curve=[];trades=0
    for i in range(max(1,start),len(idx)):
        desired=target.iloc[i];date=idx[i]
        price=lambda s,col="open": float(data[s].reindex(idx)[col].iloc[i]) if s in data and pd.notna(data[s].reindex(idx)[col].iloc[i]) else 0.
        if symbol and desired!=symbol:
            px=price(symbol)*(1-SLIP);cash+=qty*px*(1-FEE);symbol=None;qty=0;trades+=1
        if not symbol and desired!="CASH":
            px=price(desired)*(1+SLIP);lot=LOTS[desired]
            if px <= 0:
                curve.append(cash)
                continue
            lots=int(cash//(px*lot*(1+FEE)))
            if lots>0:
                qty=lots*lot;cash-=qty*px*(1+FEE);symbol=desired;trades+=1
        value=cash+(qty*price(symbol,"close") if symbol else 0);curve.append(value)
    eq=pd.Series(curve,dtype=float);years=max(len(eq)/252,1/252);cagr=(eq.iloc[-1]/INITIAL)**(1/years)-1
    dd=(eq/eq.cummax()-1).min();r=eq.pct_change().dropna();sh=np.sqrt(252)*r.mean()/r.std() if r.std()>0 else 0.
    return cagr,dd,sh,trades,eq.iloc[-1]


def main():
    cache=Path("scratch/yf_cache");cache.mkdir(exist_ok=True);yf.set_tz_cache_location(str(cache.resolve()))
    symbols=list(LOTS);raw=yf.download(symbols,period="max",interval="1d",auto_adjust=True,group_by="ticker",progress=False,threads=True)
    data={s:raw[s].rename(columns=str.lower).dropna(subset=["open","close"])[["open","high","low","close","volume"]] for s in symbols}
    common=data["3033.HK"].index.intersection(data["3067.HK"].index);split=int(len(common)*.6);rows=[]
    for mode,(fast,slow),mom,reb in itertools.product(["rotation","3067_only"],[(10,30),(20,50),(50,200)],[20,60,120],[5,10,20]):
        t=targets(data,fast,slow,mom,reb,mode)
        tr=run({s:d.loc[:common[split]] for s,d in data.items()},t.loc[:common[split]],0)
        te=run(data,t,split)
        rows.append({"mode":mode,"fast":fast,"slow":slow,"momentum":mom,"rebalance":reb,
                     "train_cagr":tr[0],"train_dd":tr[1],"train_sharpe":tr[2],"train_trades":tr[3],"train_final_hkd":tr[4],
                     "test_cagr":te[0],"test_dd":te[1],"test_sharpe":te[2],"test_trades":te[3],"test_final_hkd":te[4]})
    out=pd.DataFrame(rows);out["score"]=out.train_sharpe+out.train_cagr-out.train_dd.abs()*.25
    out.loc[out.train_trades<4,"score"]=-np.inf;selected=out.sort_values("score",ascending=False).head(20)
    selected.to_csv("scratch/hk_affordable_etf_rotation_results.csv",index=False);print(selected.to_string(index=False))


if __name__=="__main__":main()
