"""Walk-forward event strategies for HK inverse ETFs.

Tests sparse short-duration entries rather than continuously holding leveraged
inverse products: volatility shock, downside continuation, and failed rebound.
"""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import yfinance as yf

PAIRS = {"^HSI": "7500.HK", "3033.HK": "7552.HK"}
FEE, SLIP = 0.0012, 0.0005


def event_signal(df, kind, lookback, threshold, regime, confirm):
    c = df.close
    bear = c < c.rolling(regime).mean()
    if kind == "shock":
        ret = c.pct_change(lookback)
        rv_fast = c.pct_change().rolling(10).std()
        rv_slow = c.pct_change().rolling(60).std()
        signal = bear & (ret <= -threshold) & (rv_fast >= rv_slow * confirm)
    elif kind == "continuation":
        prior_low = df.low.shift(1).rolling(lookback).min()
        ret = c.pct_change(max(2, lookback // 2))
        signal = bear & (c < prior_low) & (ret <= -threshold)
    else:  # failed rebound inside a long-term downtrend
        rebound = c.shift(1).pct_change(lookback) >= threshold
        rejection = (c < c.shift(1)) & (c < c.ewm(span=5, adjust=False).mean())
        signal = bear & rebound & rejection
    # Enter only on the first day of each event cluster.
    previous = signal.shift(1, fill_value=False).astype(bool)
    return (signal.astype(bool) & ~previous).fillna(False)


def run(under, etf, signal, start, hold, sl, tp):
    idx = under.index.intersection(etf.index)
    x = etf.loc[idx]; signal = signal.reindex(idx).fillna(False)
    cash=1.; units=0.; entry=ev=0.; age=trades=wins=0; curve=[]
    for i in range(max(1,start),len(idx)):
        o,h,l,c=(float(x.iloc[i][k]) for k in ("open","high","low","close")); out=None
        if units:
            age += 1
            if l <= entry*(1-sl): out=min(o,entry*(1-sl))
            elif h >= entry*(1+tp): out=max(o,entry*(1+tp))
            elif age >= hold: out=o
        if out is not None:
            proceeds=units*out*(1-SLIP)*(1-FEE); wins+=proceeds>ev
            cash,units,trades=proceeds,0.,trades+1
        if not units and bool(signal.iloc[i-1]):
            entry=o*(1+SLIP); ev=cash; units=cash*(1-FEE)/entry; cash=0.; age=0
        curve.append(cash+units*c)
    if units:
        proceeds=units*float(x.close.iloc[-1])*(1-SLIP)*(1-FEE); wins+=proceeds>ev; trades+=1
    eq=pd.Series(curve,dtype=float); years=max(len(eq)/252,1/252)
    cagr=eq.iloc[-1]**(1/years)-1; dd=(eq/eq.cummax()-1).min(); r=eq.pct_change().dropna()
    sharpe=np.sqrt(252)*r.mean()/r.std() if r.std()>0 else 0.
    return cagr,dd,sharpe,trades,wins/trades if trades else np.nan


def main():
    cache=Path("scratch/yf_cache"); cache.mkdir(exist_ok=True); yf.set_tz_cache_location(str(cache.resolve()))
    symbols=list(PAIRS)+list(PAIRS.values())
    raw=yf.download(symbols,period="max",interval="1d",auto_adjust=True,group_by="ticker",progress=False,threads=True)
    data={s:raw[s].rename(columns=str.lower).dropna(subset=["open","close"])[["open","high","low","close","volume"]] for s in symbols}
    rows=[]
    for kind in ("shock","continuation","failed_rebound"):
      for lookback,threshold,regime,confirm,hold,sl,tp in itertools.product(
          [3,5],[.02,.04],[100,200],[1.25],[1,3],[.05],[.08]):
        vals={"train":[],"test":[]}
        for us,xs in PAIRS.items():
            u,x=data[us],data[xs]; common=u.index.intersection(x.index); split=int(len(common)*.6)
            sig=event_signal(u,kind,lookback,threshold,regime,confirm)
            vals["train"].append(run(u.loc[:common[split]],x.loc[:common[split]],sig,0,hold,sl,tp))
            vals["test"].append(run(u,x,sig,split,hold,sl,tp))
        row={"kind":kind,"lookback":lookback,"threshold":threshold,"regime":regime,"confirm":confirm,
             "hold":hold,"sl":sl,"tp":tp}
        for segment,a in vals.items():
            a=np.asarray(a,float)
            row.update({f"cagr_{segment}":np.nanmean(a[:,0]),f"worst_{segment}":np.nanmin(a[:,0]),
                        f"dd_{segment}":np.nanmean(a[:,1]),f"sharpe_{segment}":np.nanmean(a[:,2]),
                        f"trades_{segment}":np.nansum(a[:,3]),f"win_{segment}":np.nansum(a[:,4]*a[:,3])/max(np.nansum(a[:,3]),1)})
        rows.append(row)
    out=pd.DataFrame(rows)
    out["score"]=out.cagr_train+out.sharpe_train*.15-out.dd_train.abs()*.25
    out.loc[(out.trades_train<10)|(out.worst_train<=-.10),"score"]=-np.inf
    selected=out.sort_values("score",ascending=False).groupby("kind").head(10)
    selected.to_csv("scratch/hk_etf_event_results.csv",index=False)
    print(selected.to_string(index=False))


if __name__ == "__main__": main()
