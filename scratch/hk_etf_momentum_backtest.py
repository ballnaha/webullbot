"""Walk-forward test of self-confirming momentum for HK inverse ETFs."""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import yfinance as yf

PAIRS = {"^HSI": "7500.HK", "3033.HK": "7552.HK"}
FEE, SLIP = 0.0012, 0.0005


def signals(under, etf, regime, fast, slow, breakout, exit_fast):
    uc, xc = under.close, etf.close
    bear = uc < uc.rolling(regime).mean()
    momentum = xc.ewm(span=fast, adjust=False).mean() > xc.ewm(span=slow, adjust=False).mean()
    new_high = xc >= xc.shift(1).rolling(breakout).max()
    enter = bear & momentum & new_high
    leave = (~bear) | (xc < xc.ewm(span=exit_fast, adjust=False).mean())
    return enter.fillna(False), leave.fillna(False)


def run(under, etf, enter, leave, start, sl, trail, hold):
    idx = under.index.intersection(etf.index)
    x = etf.loc[idx]; enter = enter.reindex(idx).fillna(False); leave = leave.reindex(idx).fillna(False)
    cash=1.; units=0.; entry=peak=ev=0.; age=trades=wins=0; curve=[]
    for i in range(max(1,start), len(idx)):
        o,h,l,c = (float(x.iloc[i][k]) for k in ("open","high","low","close")); out=None
        if units:
            age += 1; peak=max(peak,h)
            if l <= entry*(1-sl): out=min(o,entry*(1-sl))
            elif l <= peak*(1-trail): out=min(o,peak*(1-trail))
            elif bool(leave.iloc[i-1]) or age>=hold: out=o
        if out is not None:
            proceeds=units*out*(1-SLIP)*(1-FEE); wins += proceeds>ev
            cash,units,trades=proceeds,0.,trades+1
        if not units and bool(enter.iloc[i-1]):
            entry=o*(1+SLIP); peak=entry; ev=cash
            units=cash*(1-FEE)/entry; cash=0.; age=0
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
    rows=[]; keys=["regime","fast","slow","breakout","exit_fast","sl","trail","hold"]
    # Compact, economically distinct grid keeps the walk-forward reproducible
    # without mining thousands of near-identical parameter combinations.
    grid=itertools.product([100,200],[3,5],[10,20],[5,10],[3,5],[.05],[.03,.05],[3,5,10])
    for regime,fast,slow,breakout,exit_fast,sl,trail,hold in grid:
        if fast>=slow: continue
        vals={"train":[],"test":[]}
        for us,xs in PAIRS.items():
            u,x=data[us],data[xs]; common=u.index.intersection(x.index); split=int(len(common)*.6)
            enter,leave=signals(u,x,regime,fast,slow,breakout,exit_fast)
            vals["train"].append(run(u.loc[:common[split]],x.loc[:common[split]],enter,leave,0,sl,trail,hold))
            vals["test"].append(run(u,x,enter,leave,split,sl,trail,hold))
        row=dict(zip(keys,[regime,fast,slow,breakout,exit_fast,sl,trail,hold]))
        for segment,a in vals.items():
            a=np.asarray(a,float)
            row.update({f"cagr_{segment}":np.nanmean(a[:,0]),f"worst_{segment}":np.nanmin(a[:,0]),
                        f"dd_{segment}":np.nanmean(a[:,1]),f"sharpe_{segment}":np.nanmean(a[:,2]),
                        f"trades_{segment}":np.nansum(a[:,3]),f"win_{segment}":np.nansum(a[:,4]*a[:,3])/max(np.nansum(a[:,3]),1)})
        rows.append(row)
    out=pd.DataFrame(rows)
    out["score"]=out.cagr_train+out.sharpe_train*.2-out.dd_train.abs()*.25
    out.loc[(out.trades_train<12)|(out.worst_train<=-0.10),"score"]=-np.inf
    chosen=out.sort_values("score",ascending=False).head(20)
    chosen.to_csv("scratch/hk_etf_momentum_results.csv",index=False)
    print(chosen.to_string(index=False))


if __name__ == "__main__": main()
