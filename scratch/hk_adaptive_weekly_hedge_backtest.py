"""Walk-forward adaptive drawdown and weekly-regime HK inverse ETF overlays."""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import yfinance as yf

PAIRS={"7500.HK":"2800.HK","7552.HK":"3033.HK"}
COST=.0017


def weights(long_df,kind,entry,high,exit_level,weekly_fast,weekly_slow):
    c=long_df.close
    if kind=="drawdown":
        dd=c/c.cummax()-1
        w=pd.Series(0.,index=c.index)
        active=0.
        for i,value in enumerate(dd):
            if value<=-high: active=.50
            elif value<=-entry: active=.25
            elif value>=-exit_level: active=0.
            w.iloc[i]=active
    else:
        weekly=c.resample("W-FRI").last()
        bear=(weekly.ewm(span=weekly_fast,adjust=False).mean()<weekly.ewm(span=weekly_slow,adjust=False).mean())
        severe=weekly.pct_change(4)<-high
        ww=pd.Series(0.,index=weekly.index);ww[bear]=.25;ww[bear&severe]=.50
        w=ww.reindex(c.index,method="ffill").fillna(0.)
    return w.shift(1).fillna(0.)


def evaluate(long_df,inv_df,w,start):
    idx=long_df.index.intersection(inv_df.index).intersection(w.index)
    lr=long_df.close.reindex(idx).pct_change().fillna(0).iloc[start:]
    xr=inv_df.close.reindex(idx).pct_change().fillna(0).iloc[start:]
    wt=w.reindex(idx).fillna(0).iloc[start:]
    turn=wt.diff().abs().fillna(wt.abs())
    base=(1+lr).cumprod(); hedge=(1+(1-wt)*lr+wt*xr-turn*COST).cumprod()
    cash=(1+(1-wt*2)*lr-turn*2*COST).cumprod()
    def m(eq):
        years=max(len(eq)/252,1/252);cg=eq.iloc[-1]**(1/years)-1;dd=(eq/eq.cummax()-1).min()
        r=eq.pct_change().dropna();sh=np.sqrt(252)*r.mean()/r.std() if r.std()>0 else 0.
        return cg,dd,sh
    return m(base),m(hedge),m(cash),int((turn>0).sum()),float(wt.mean())


def main():
    cache=Path("scratch/yf_cache");cache.mkdir(exist_ok=True);yf.set_tz_cache_location(str(cache.resolve()))
    symbols=list(PAIRS)+list(PAIRS.values())
    raw=yf.download(symbols,period="max",interval="1d",auto_adjust=True,group_by="ticker",progress=False,threads=True)
    data={s:raw[s].rename(columns=str.lower).dropna(subset=["close"])[["open","high","low","close","volume"]] for s in symbols}
    rows=[]
    configs=[]
    for entry,high,ex in itertools.product([.05,.08,.10],[.12,.15,.20],[.02,.04]):
        if entry<high: configs.append(("drawdown",entry,high,ex,0,0))
    for wf,ws,severe in itertools.product([3,5,10],[10,20,30],[.04,.06,.08]):
        if wf<ws: configs.append(("weekly",0,severe,0,wf,ws))
    for kind,entry,high,ex,wf,ws in configs:
        row={"kind":kind,"entry":entry,"high":high,"exit":ex,"weekly_fast":wf,"weekly_slow":ws}
        for seg in ("train","test"):
            vals=[]
            for inv,long in PAIRS.items():
                common=data[long].index.intersection(data[inv].index);split=int(len(common)*.6)
                w=weights(data[long],kind,entry,high,ex,wf,ws)
                vals.append(evaluate(data[long].loc[:common[split]],data[inv].loc[:common[split]],w,0) if seg=="train" else evaluate(data[long],data[inv],w,split))
            for name,pos in (("base",0),("hedge",1),("cash",2)):
                a=np.asarray([v[pos] for v in vals]);row.update({f"{name}_cagr_{seg}":a[:,0].mean(),f"{name}_dd_{seg}":a[:,1].mean(),f"{name}_sharpe_{seg}":a[:,2].mean()})
            row[f"switches_{seg}"]=sum(v[3] for v in vals);row[f"weight_{seg}"]=np.mean([v[4] for v in vals])
        rows.append(row)
    out=pd.DataFrame(rows)
    for mode in ("hedge","cash"):
        out[f"{mode}_score_train"]=(out[f"{mode}_dd_train"]-out.base_dd_train)+(out[f"{mode}_cagr_train"]-out.base_cagr_train)*.5
    out["winner_train"]=np.where(out.hedge_score_train>=out.cash_score_train,"hedge","cash")
    out["score"]=out[["hedge_score_train","cash_score_train"]].max(axis=1)
    out.loc[out.switches_train<4,"score"]=-np.inf
    selected=out.sort_values("score",ascending=False).groupby("kind").head(10)
    selected.to_csv("scratch/hk_adaptive_weekly_hedge_results.csv",index=False)
    print(selected.to_string(index=False))


if __name__=="__main__":main()
