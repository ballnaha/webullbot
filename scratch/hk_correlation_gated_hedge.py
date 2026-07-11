"""Walk-forward weekly hedge gated by inverse correlation and tracking quality."""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import yfinance as yf

PAIRS={"7500.HK":"2800.HK","7552.HK":"3033.HK"}
COST=.0017


def weights(long_df,inv_df,fast,slow,window,corr_max,tracking_min,weight,cooldown):
    idx=long_df.index.intersection(inv_df.index);l=long_df.close.reindex(idx);x=inv_df.close.reindex(idx)
    lr=l.pct_change();xr=x.pct_change();corr=lr.rolling(window).corr(xr)
    # Magnitude of inverse response per 1% move in the long tracker.
    beta=(xr.rolling(window).cov(lr)/lr.rolling(window).var()).abs()
    weekly=l.resample("W-FRI").last();bear=weekly.ewm(span=fast,adjust=False).mean()<weekly.ewm(span=slow,adjust=False).mean()
    regime=bear.astype(bool).reindex(idx,method="ffill").astype("boolean").fillna(False).astype(bool)
    allowed=regime&(corr<=corr_max)&(beta>=tracking_min)
    out=pd.Series(0.,index=idx);active=False;cool=0
    for i,ok in enumerate(allowed.fillna(False)):
        # Re-evaluate only weekly to prevent noisy daily weight changes.
        if i%5==0:
            if active and not ok:active=False;cool=cooldown
            elif not active:
                if cool>0:cool-=5
                elif ok:active=True
        out.iloc[i]=weight if active else 0.
    return out.shift(1).fillna(0.)


def evaluate(long_df,inv_df,w,start):
    idx=long_df.index.intersection(inv_df.index).intersection(w.index)
    lr=long_df.close.reindex(idx).pct_change().fillna(0).iloc[start:];xr=inv_df.close.reindex(idx).pct_change().fillna(0).iloc[start:]
    wt=w.reindex(idx).fillna(0).iloc[start:];turn=wt.diff().abs().fillna(wt.abs())
    base=(1+lr).cumprod();eq=(1+(1-wt)*lr+wt*xr-turn*COST).cumprod()
    def m(v):
        years=max(len(v)/252,1/252);cg=v.iloc[-1]**(1/years)-1;dd=(v/v.cummax()-1).min();r=v.pct_change().dropna()
        sh=np.sqrt(252)*r.mean()/r.std() if r.std()>0 else 0.;return cg,dd,sh
    return m(base),m(eq),int((turn>0).sum()),float(wt.mean())


def main():
    cache=Path("scratch/yf_cache");cache.mkdir(exist_ok=True);yf.set_tz_cache_location(str(cache.resolve()))
    symbols=list(PAIRS)+list(PAIRS.values());raw=yf.download(symbols,period="max",interval="1d",auto_adjust=True,group_by="ticker",progress=False,threads=True)
    data={s:raw[s].rename(columns=str.lower).dropna(subset=["close"])[["open","high","low","close","volume"]] for s in symbols}
    rows=[]
    for fast,slow,window,corr,track,w,cool in itertools.product([3,5,10],[10,20,30],[20,60],[-.3,-.5,-.7],[.5,1.0],[.1,.2,.25],[5,10]):
        if fast>=slow:continue
        row={"fast":fast,"slow":slow,"window":window,"corr_max":corr,"tracking_min":track,"weight":w,"cooldown":cool}
        for seg in ("train","test"):
            vals=[]
            for inv,long in PAIRS.items():
                common=data[long].index.intersection(data[inv].index);split=int(len(common)*.6)
                wt=weights(data[long],data[inv],fast,slow,window,corr,track,w,cool)
                vals.append(evaluate(data[long].loc[:common[split]],data[inv].loc[:common[split]],wt,0) if seg=="train" else evaluate(data[long],data[inv],wt,split))
            b=np.asarray([v[0] for v in vals]);h=np.asarray([v[1] for v in vals])
            row.update({f"base_cagr_{seg}":b[:,0].mean(),f"base_dd_{seg}":b[:,1].mean(),f"base_sharpe_{seg}":b[:,2].mean(),
                        f"hedge_cagr_{seg}":h[:,0].mean(),f"hedge_dd_{seg}":h[:,1].mean(),f"hedge_sharpe_{seg}":h[:,2].mean(),
                        f"switches_{seg}":sum(v[2] for v in vals),f"exposure_{seg}":np.mean([v[3] for v in vals])})
        rows.append(row)
    out=pd.DataFrame(rows);out["cagr_delta_train"]=out.hedge_cagr_train-out.base_cagr_train;out["dd_delta_train"]=out.hedge_dd_train-out.base_dd_train
    out["sharpe_delta_train"]=out.hedge_sharpe_train-out.base_sharpe_train
    out["score"]=out.dd_delta_train+out.cagr_delta_train*.5+out.sharpe_delta_train*.1
    out.loc[(out.switches_train<4)|(out.cagr_delta_train<-.05),"score"]=-np.inf
    selected=out.sort_values("score",ascending=False).head(20);selected.to_csv("scratch/hk_correlation_gated_results.csv",index=False)
    print(selected.to_string(index=False))


if __name__=="__main__":main()
