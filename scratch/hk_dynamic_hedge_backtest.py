"""Walk-forward breadth + relative-strength dynamic hedge for HK ETFs."""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import yfinance as yf

GROUPS = {
    "7500.HK": ("2800.HK", ["0700.HK","9988.HK","2318.HK","0388.HK","1299.HK","0005.HK","0941.HK","3988.HK"]),
    "7552.HK": ("3033.HK", ["1810.HK","3690.HK","9618.HK","1024.HK","9888.HK","2015.HK","1211.HK"]),
}
COST = .0012 + .0005


def hedge_weights(long_df, inv_df, constituents, fast, slow, rs_window, breadth_mid, breadth_high):
    states=[]
    for d in constituents:
        c=d.close
        states.append((c.rolling(fast).mean() < c.rolling(slow).mean()).rename(c.name))
    breadth=pd.concat(states,axis=1).mean(axis=1)
    idx=long_df.index.intersection(inv_df.index)
    ratio=(inv_df.close.reindex(idx)/long_df.close.reindex(idx)).replace([np.inf,-np.inf],np.nan)
    rs=ratio.pct_change(rs_window)>0
    b=pd.to_numeric(breadth.reindex(idx),errors="coerce").ffill()
    weight=pd.Series(0.,index=idx)
    weight[(b>=breadth_mid)&rs]=.25
    weight[(b>=breadth_high)&rs]=.50
    return weight.shift(1).fillna(0.)


def evaluate(long_df, inv_df, weight, start=0):
    idx=long_df.index.intersection(inv_df.index).intersection(weight.index)
    lr=long_df.close.reindex(idx).pct_change().fillna(0).iloc[start:]
    xr=inv_df.close.reindex(idx).pct_change().fillna(0).iloc[start:]
    w=weight.reindex(idx).fillna(0).iloc[start:]
    turnover=w.diff().abs().fillna(w.abs())
    base=(1+lr).cumprod()
    port_r=(1-w)*lr+w*xr-turnover*COST
    hedge=(1+port_r).cumprod()
    def m(eq):
        years=max(len(eq)/252,1/252); cagr=eq.iloc[-1]**(1/years)-1
        dd=(eq/eq.cummax()-1).min(); r=eq.pct_change().dropna()
        sharpe=np.sqrt(252)*r.mean()/r.std() if r.std()>0 else 0.
        return cagr,dd,sharpe
    return m(base),m(hedge),int((turnover>0).sum()),float(w.mean())


def main():
    cache=Path("scratch/yf_cache");cache.mkdir(exist_ok=True);yf.set_tz_cache_location(str(cache.resolve()))
    symbols=sorted(set(GROUPS)|{v[0] for v in GROUPS.values()}|{s for _,stocks in GROUPS.values() for s in stocks})
    raw=yf.download(symbols,period="10y",interval="1d",auto_adjust=True,group_by="ticker",progress=False,threads=True)
    data={}
    for s in symbols:
        d=raw[s].rename(columns=str.lower).dropna(subset=["close"])
        if len(d):
            d=d[["open","high","low","close","volume"]]; d.close.name=s; data[s]=d
    rows=[]
    for fast,slow,rsw,bmid,bhigh in itertools.product([5,10,20],[20,50],[3,5,10],[.50,.60],[.70,.80]):
        if fast>=slow or bmid>=bhigh: continue
        row={"fast":fast,"slow":slow,"rs_window":rsw,"breadth_mid":bmid,"breadth_high":bhigh}
        for segment in ("train","test"):
            vals=[]
            for inv,(long,stocks) in GROUPS.items():
                available=[data[s] for s in stocks if s in data]
                common=data[long].index.intersection(data[inv].index); split=int(len(common)*.6)
                w=hedge_weights(data[long],data[inv],available,fast,slow,rsw,bmid,bhigh)
                vals.append(evaluate(data[long].loc[:common[split]],data[inv].loc[:common[split]],w,0) if segment=="train"
                            else evaluate(data[long],data[inv],w,split))
            base=np.asarray([v[0] for v in vals]); hedge=np.asarray([v[1] for v in vals])
            row.update({f"base_cagr_{segment}":base[:,0].mean(),f"base_dd_{segment}":base[:,1].mean(),
                        f"hedge_cagr_{segment}":hedge[:,0].mean(),f"hedge_dd_{segment}":hedge[:,1].mean(),
                        f"hedge_sharpe_{segment}":hedge[:,2].mean(),f"switches_{segment}":sum(v[2] for v in vals),
                        f"avg_weight_{segment}":np.mean([v[3] for v in vals])})
        rows.append(row)
    out=pd.DataFrame(rows)
    out["cagr_delta_train"]=out.hedge_cagr_train-out.base_cagr_train
    out["dd_delta_train"]=out.hedge_dd_train-out.base_dd_train
    # Primary objective is drawdown reduction, but reject severe return sacrifice.
    out["score"]=out.dd_delta_train+out.cagr_delta_train*.5+out.hedge_sharpe_train*.05
    out.loc[(out.switches_train<10)|(out.cagr_delta_train<-.08),"score"]=-np.inf
    selected=out.sort_values("score",ascending=False).head(20)
    selected.to_csv("scratch/hk_dynamic_hedge_results.csv",index=False)
    print(selected.to_string(index=False))


if __name__=="__main__": main()
