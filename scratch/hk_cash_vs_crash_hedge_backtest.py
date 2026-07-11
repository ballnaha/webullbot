"""Walk-forward comparison: long-only, risk-off cash, and crash-only inverse hedge."""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import yfinance as yf

GROUPS={
 "7500.HK":("2800.HK",["0700.HK","9988.HK","2318.HK","0388.HK","1299.HK","0005.HK","0941.HK","3988.HK"]),
 "7552.HK":("3033.HK",["1810.HK","3690.HK","9618.HK","1024.HK","9888.HK","2015.HK","1211.HK"]),
}
COST=.0017


def risk_state(long_df, constituents, fast, slow, enter_breadth, exit_breadth, drop5, vol_ratio, cooldown):
    states=[]
    for d in constituents:
        c=d.close
        states.append((c.rolling(fast).mean()<c.rolling(slow).mean()).astype(float))
    breadth=pd.concat(states,axis=1).mean(axis=1).reindex(long_df.index).ffill()
    c=long_df.close
    regime=c<c.rolling(200).mean()
    shock=c.pct_change(5)<=-drop5
    rv10=c.pct_change().rolling(10).std()
    rv60=c.pct_change().rolling(60).std()
    vol=rv10>=rv60*vol_ratio
    enter=regime&(breadth>=enter_breadth)&(shock|vol)
    leave=(breadth<=exit_breadth)|(c>c.ewm(span=10,adjust=False).mean())
    active=False; cool=0; out=[]
    for en,ex in zip(enter.fillna(False),leave.fillna(True)):
        if active and ex: active=False; cool=cooldown
        elif not active:
            if cool>0: cool-=1
            elif en: active=True
        out.append(active)
    return pd.Series(out,index=long_df.index,dtype=bool).shift(1,fill_value=False)


def evaluate(long_df,inv_df,risk,start,hedge_weight):
    idx=long_df.index.intersection(inv_df.index).intersection(risk.index)
    lr=long_df.close.reindex(idx).pct_change().fillna(0).iloc[start:]
    xr=inv_df.close.reindex(idx).pct_change().fillna(0).iloc[start:]
    state=risk.reindex(idx).fillna(False).astype(float).iloc[start:]
    changes=state.diff().abs().fillna(state.abs())
    base=(1+lr).cumprod()
    cash_r=(1-state)*lr-changes*COST
    hedge_r=(1-state*hedge_weight)*lr+state*hedge_weight*xr-changes*hedge_weight*COST
    cash=(1+cash_r).cumprod(); hedge=(1+hedge_r).cumprod()
    def m(eq):
        years=max(len(eq)/252,1/252); cagr=eq.iloc[-1]**(1/years)-1
        dd=(eq/eq.cummax()-1).min(); r=eq.pct_change().dropna()
        sh=np.sqrt(252)*r.mean()/r.std() if r.std()>0 else 0.
        return cagr,dd,sh
    return m(base),m(cash),m(hedge),int(changes.sum()),float(state.mean())


def main():
    cache=Path("scratch/yf_cache");cache.mkdir(exist_ok=True);yf.set_tz_cache_location(str(cache.resolve()))
    symbols=sorted(set(GROUPS)|{v[0] for v in GROUPS.values()}|{s for _,ss in GROUPS.values() for s in ss})
    raw=yf.download(symbols,period="10y",interval="1d",auto_adjust=True,group_by="ticker",progress=False,threads=True)
    data={s:raw[s].rename(columns=str.lower).dropna(subset=["close"])[["open","high","low","close","volume"]] for s in symbols if len(raw[s].dropna(how="all"))}
    rows=[]
    for fast,slow,eb,xb,drop,vr,cd,hw in itertools.product([5,10],[20,50],[.7,.8],[.4,.5],[.03,.05],[1.,1.25],[5,10],[.25,.5]):
        if fast>=slow or xb>=eb: continue
        row={"fast":fast,"slow":slow,"enter_breadth":eb,"exit_breadth":xb,"drop5":drop,"vol_ratio":vr,"cooldown":cd,"hedge_weight":hw}
        for seg in ("train","test"):
            vals=[]
            for inv,(long,stocks) in GROUPS.items():
                common=data[long].index.intersection(data[inv].index); split=int(len(common)*.6)
                risk=risk_state(data[long],[data[s] for s in stocks if s in data],fast,slow,eb,xb,drop,vr,cd)
                vals.append(evaluate(data[long].loc[:common[split]],data[inv].loc[:common[split]],risk,0,hw) if seg=="train" else evaluate(data[long],data[inv],risk,split,hw))
            for name,pos in (("base",0),("cash",1),("hedge",2)):
                a=np.asarray([v[pos] for v in vals])
                row.update({f"{name}_cagr_{seg}":a[:,0].mean(),f"{name}_dd_{seg}":a[:,1].mean(),f"{name}_sharpe_{seg}":a[:,2].mean()})
            row[f"switches_{seg}"]=sum(v[3] for v in vals);row[f"risk_time_{seg}"]=np.mean([v[4] for v in vals])
        rows.append(row)
    out=pd.DataFrame(rows)
    out["cash_score_train"]=(out.cash_dd_train-out.base_dd_train)+(out.cash_cagr_train-out.base_cagr_train)*.5
    out["hedge_score_train"]=(out.hedge_dd_train-out.base_dd_train)+(out.hedge_cagr_train-out.base_cagr_train)*.5
    out["winner_train"]=np.where(out.cash_score_train>=out.hedge_score_train,"cash","hedge")
    out["score"]=out[["cash_score_train","hedge_score_train"]].max(axis=1)
    out.loc[out.switches_train<6,"score"]=-np.inf
    selected=out.sort_values("score",ascending=False).head(20)
    selected.to_csv("scratch/hk_cash_vs_crash_hedge_results.csv",index=False)
    print(selected.to_string(index=False))


if __name__=="__main__":main()
