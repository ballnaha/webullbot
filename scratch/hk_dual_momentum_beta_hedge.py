"""Walk-forward monthly dual momentum and beta-scaled weekly HK ETF hedge."""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import yfinance as yf

PAIRS={"7500.HK":"2800.HK","7552.HK":"3033.HK"}
COST=.0017


def dual_weights(long_df,inv_df,lookback,rebalance,buffer):
    idx=long_df.index.intersection(inv_df.index);l=long_df.close.reindex(idx);x=inv_df.close.reindex(idx)
    lm=l.pct_change(lookback);xm=x.pct_change(lookback)
    target=pd.Series(0.,index=idx) # -1 inverse, 0 cash, +1 long
    target[(lm>buffer)&(lm>=xm)]=1.;target[(xm>buffer)&(xm>lm)]=-1.
    out=pd.Series(0.,index=idx);current=0.
    for i in range(len(idx)):
        if i%rebalance==0:current=float(target.iloc[i])
        out.iloc[i]=current
    return out.shift(1).fillna(0.)


def beta_weights(long_df,inv_df,fast,slow,beta_window,cap):
    idx=long_df.index.intersection(inv_df.index);l=long_df.close.reindex(idx);x=inv_df.close.reindex(idx)
    lr=l.pct_change();xr=x.pct_change()
    beta=(lr.rolling(beta_window).cov(xr)/xr.rolling(beta_window).var()).abs().clip(0,cap)
    weekly=l.resample("W-FRI").last();bear=(weekly.ewm(span=fast,adjust=False).mean()<weekly.ewm(span=slow,adjust=False).mean())
    regime=bear.astype(bool).reindex(idx,method="ffill").astype("boolean").fillna(False).astype(bool)
    return beta.where(regime,0.).shift(1).fillna(0.)


def evaluate(long_df,inv_df,w,start,kind):
    idx=long_df.index.intersection(inv_df.index).intersection(w.index)
    lr=long_df.close.reindex(idx).pct_change().fillna(0).iloc[start:];xr=inv_df.close.reindex(idx).pct_change().fillna(0).iloc[start:]
    wt=w.reindex(idx).fillna(0).iloc[start:];base=(1+lr).cumprod()
    if kind=="dual":
        pr=np.where(wt>0,lr,np.where(wt<0,xr,0.));turn=wt.diff().abs().fillna(wt.abs())/2
    else:
        pr=(1-wt)*lr+wt*xr;turn=wt.diff().abs().fillna(wt.abs())
    eq=(1+pd.Series(pr,index=lr.index)-turn*COST).cumprod()
    def m(v):
        years=max(len(v)/252,1/252);cg=v.iloc[-1]**(1/years)-1;dd=(v/v.cummax()-1).min();r=v.pct_change().dropna()
        sh=np.sqrt(252)*r.mean()/r.std() if r.std()>0 else 0.;return cg,dd,sh
    return m(base),m(eq),int((turn>0).sum()),float(wt.abs().mean())


def main():
    cache=Path("scratch/yf_cache");cache.mkdir(exist_ok=True);yf.set_tz_cache_location(str(cache.resolve()))
    symbols=list(PAIRS)+list(PAIRS.values());raw=yf.download(symbols,period="max",interval="1d",auto_adjust=True,group_by="ticker",progress=False,threads=True)
    data={s:raw[s].rename(columns=str.lower).dropna(subset=["close"])[["open","high","low","close","volume"]] for s in symbols}
    configs=[]
    for lb,reb,buf in itertools.product([20,60,120],[5,10,20],[0,.02,.05]):configs.append(("dual",lb,reb,buf,0,0))
    for f,s,bw,cap in itertools.product([3,5,10],[10,20,30],[20,60],[.25,.5]):
        if f<s:configs.append(("beta",f,s,bw,cap,0))
    rows=[]
    for kind,a,b,c,d,_ in configs:
        row={"kind":kind,"a":a,"b":b,"c":c,"d":d}
        for seg in ("train","test"):
            vals=[]
            for inv,long in PAIRS.items():
                common=data[long].index.intersection(data[inv].index);split=int(len(common)*.6)
                w=dual_weights(data[long],data[inv],a,b,c) if kind=="dual" else beta_weights(data[long],data[inv],a,b,c,d)
                vals.append(evaluate(data[long].loc[:common[split]],data[inv].loc[:common[split]],w,0,kind) if seg=="train" else evaluate(data[long],data[inv],w,split,kind))
            base=np.asarray([v[0] for v in vals]);strategy=np.asarray([v[1] for v in vals])
            row.update({f"base_cagr_{seg}":base[:,0].mean(),f"base_dd_{seg}":base[:,1].mean(),f"base_sharpe_{seg}":base[:,2].mean(),
                        f"strategy_cagr_{seg}":strategy[:,0].mean(),f"strategy_dd_{seg}":strategy[:,1].mean(),f"strategy_sharpe_{seg}":strategy[:,2].mean(),
                        f"switches_{seg}":sum(v[2] for v in vals),f"exposure_{seg}":np.mean([v[3] for v in vals])})
        rows.append(row)
    out=pd.DataFrame(rows);out["cagr_delta_train"]=out.strategy_cagr_train-out.base_cagr_train;out["dd_delta_train"]=out.strategy_dd_train-out.base_dd_train
    out["score"]=out.dd_delta_train+out.cagr_delta_train*.5+(out.strategy_sharpe_train-out.base_sharpe_train)*.05
    out.loc[out.switches_train<5,"score"]=-np.inf
    selected=out.sort_values("score",ascending=False).groupby("kind").head(10)
    selected.to_csv("scratch/hk_dual_momentum_beta_results.csv",index=False);print(selected.to_string(index=False))


if __name__=="__main__":main()
