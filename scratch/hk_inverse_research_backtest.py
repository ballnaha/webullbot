"""Compare HK inverse products using swing, intraday ORB, and hedge overlay tests."""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import yfinance as yf

FEE, SLIP = .0012, .0005


def metrics(eq, trades=0, wins=0, periods_per_year=252):
    eq = pd.Series(eq, dtype=float)
    years = max(len(eq)/periods_per_year, 1/periods_per_year)
    ret = eq.iloc[-1]**(1/years)-1
    dd = (eq/eq.cummax()-1).min()
    r = eq.pct_change().dropna()
    sharpe = np.sqrt(periods_per_year)*r.mean()/r.std() if r.std() > 0 else 0
    return ret, dd, sharpe, trades, wins/trades if trades else np.nan


def swing(under, inverse, fast, slow, vol_window, vol_max, hold, sl, tp, start=0):
    idx = under.index.intersection(inverse.index); u, x = under.loc[idx], inverse.loc[idx]
    rv = u.close.pct_change().rolling(vol_window).std()*np.sqrt(252)
    bear = (u.close < u.close.rolling(200).mean()) & (u.close.rolling(fast).mean() < u.close.rolling(slow).mean()) & (rv < vol_max)
    cash, units, entry, age, ev = 1.,0.,0.,0,0.; eq=[]; trades=wins=0
    for i in range(max(1,start),len(idx)):
        o,h,l,c=(float(x.iloc[i][z]) for z in ('open','high','low','close')); out=None
        if units:
            age+=1
            if l<=entry*(1-sl): out=min(o,entry*(1-sl))
            elif h>=entry*(1+tp): out=max(o,entry*(1+tp))
            elif not bool(bear.iloc[i-1]) or age>=hold: out=o
        if out is not None:
            proceeds=units*out*(1-SLIP)*(1-FEE); wins+=proceeds>ev; cash,units,trades=proceeds,0.,trades+1
        if not units and bool(bear.iloc[i-1]):
            entry=o*(1+SLIP); ev=cash; units=cash*(1-FEE)/entry; cash,age=0.,0
        eq.append(cash+units*c)
    return metrics(eq,trades,wins)


def orb(under, inverse, opening_minutes, vol_factor, sl, tp):
    idx=under.index.intersection(inverse.index); u,x=under.loc[idx],inverse.loc[idx]
    days=sorted(set(idx.date)); cash=1.; daily_eq=[]; trades=wins=0
    for day in days:
        loc=np.flatnonzero(idx.date==day)
        if len(loc)<20: continue
        ud=u.iloc[loc]; xd=x.iloc[loc]
        opening=max(1,opening_minutes//5)
        opening_low=float(ud.low.iloc[:opening].min())
        typical=(ud.high+ud.low+ud.close)/3
        vwap=(typical*ud.volume).cumsum()/ud.volume.cumsum().replace(0,np.nan)
        vol_avg=ud.volume.shift(1).rolling(20,min_periods=5).mean()
        trigger=(ud.close<opening_low)&(ud.close<vwap)&(ud.volume>vol_avg*vol_factor)
        candidates=np.flatnonzero(trigger.to_numpy() & (np.arange(len(ud))>=opening))
        if len(candidates):
            j=int(candidates[0])+1
            if j<len(xd)-2:
                entry=float(xd.open.iloc[j])*(1+SLIP); exit_px=float(xd.close.iloc[-2])
                for k in range(j,len(xd)-1):
                    if float(xd.low.iloc[k])<=entry*(1-sl): exit_px=min(float(xd.open.iloc[k]),entry*(1-sl)); break
                    if float(xd.high.iloc[k])>=entry*(1+tp): exit_px=max(float(xd.open.iloc[k]),entry*(1+tp)); break
                final=cash*(1-FEE)/entry*exit_px*(1-SLIP)*(1-FEE)
                wins+=final>cash; cash=final; trades+=1
        daily_eq.append(cash)
    return metrics(daily_eq,trades,wins)


def hedge_overlay(long_etf, inverse, hedge_weight, fast, slow, start=0):
    idx=long_etf.index.intersection(inverse.index); l,x=long_etf.loc[idx],inverse.loc[idx]
    bear=(l.close.rolling(fast).mean()<l.close.rolling(slow).mean()).shift(1).fillna(False).astype(bool)
    lr=l.close.pct_change().fillna(0); xr=x.close.pct_change().fillna(0)
    lr, xr, bear = lr.iloc[start:], xr.iloc[start:], bear.iloc[start:]
    baseline=(1+lr).cumprod()
    # Rebalance daily only while hedge state changes; conservative daily return blend.
    port_r=(1-hedge_weight*bear.astype(float))*lr + hedge_weight*bear.astype(float)*xr
    changes=bear.astype(int).diff().abs().fillna(0)
    port_r-=changes*hedge_weight*(FEE+SLIP)
    hedged=(1+port_r).cumprod()
    return metrics(baseline),metrics(hedged),int(changes.sum())


def download(symbols,interval,period):
    raw=yf.download(symbols,period=period,interval=interval,auto_adjust=True,group_by='ticker',progress=False,threads=True)
    out={}
    for s in symbols:
        d=raw[s].rename(columns=str.lower).dropna(subset=['open','close'])
        if len(d): out[s]=d[['open','high','low','close','volume']]
    return out


def main():
    cache=Path('scratch/yf_cache');cache.mkdir(exist_ok=True);yf.set_tz_cache_location(str(cache.resolve()))
    daily=download(['2800.HK','3033.HK','7300.HK','7500.HK','7552.HK'],'1d','max')
    rows=[]
    for inv in ['7300.HK','7500.HK']:
      for fast,slow,vol_max,hold,sl,tp in itertools.product([10,20],[30,50],[.20,.30,.40],[3,5,10],[.03,.05],[.06,.10]):
        common=daily['2800.HK'].index.intersection(daily[inv].index); split=int(len(common)*.6)
        tr=swing(daily['2800.HK'].loc[:common[split]],daily[inv].loc[:common[split]],fast,slow,20,vol_max,hold,sl,tp)
        te=swing(daily['2800.HK'],daily[inv],fast,slow,20,vol_max,hold,sl,tp,split)
        rows.append({'test':'swing','asset':inv,'params':f'{fast}/{slow},vol<{vol_max},hold{hold},sl{sl},tp{tp}','train_cagr':tr[0],'train_dd':tr[1],'test_cagr':te[0],'test_dd':te[1],'test_sharpe':te[2],'trades':te[3],'win_rate':te[4]})
    swing_df=pd.DataFrame(rows); swing_df['score']=swing_df.train_cagr+swing_df.train_dd*.25
    swing_best=swing_df.sort_values('score',ascending=False).groupby('asset').head(5)

    intraday=download(['2800.HK','3033.HK','7300.HK','7500.HK','7552.HK'],'5m','60d')
    orb_rows=[]
    pairs=[('2800.HK','7300.HK'),('2800.HK','7500.HK'),('3033.HK','7552.HK')]
    for under,inv in pairs:
      for opening,vf,sl,tp in itertools.product([15,30,60],[1.,1.2,1.5],[.01,.02],[.02,.03,.04]):
        m=orb(intraday[under],intraday[inv],opening,vf,sl,tp)
        orb_rows.append({'test':'orb','asset':inv,'params':f'open{opening},volx{vf},sl{sl},tp{tp}','cagr':m[0],'dd':m[1],'sharpe':m[2],'trades':m[3],'win_rate':m[4]})
    orb_df=pd.DataFrame(orb_rows); orb_df['score']=orb_df.sharpe+orb_df.cagr+orb_df.dd*.25
    orb_best=orb_df.sort_values('score',ascending=False).groupby('asset').head(5)

    hedge_rows=[]
    for long,inv in [('2800.HK','7300.HK'),('2800.HK','7500.HK'),('3033.HK','7552.HK')]:
      for weight,fast,slow in itertools.product([.25,.5],[10,20],[30,50]):
        common=daily[long].index.intersection(daily[inv].index); split=int(len(common)*.6)
        btr,htr,ntr=hedge_overlay(daily[long].loc[:common[split]],daily[inv].loc[:common[split]],weight,fast,slow)
        bte,hte,nte=hedge_overlay(daily[long],daily[inv],weight,fast,slow,split)
        hedge_rows.append({'long':long,'inverse':inv,'weight':weight,'ma':f'{fast}/{slow}',
          'baseline_cagr_train':btr[0],'baseline_dd_train':btr[1],'hedged_cagr_train':htr[0],'hedged_dd_train':htr[1],
          'baseline_cagr_test':bte[0],'baseline_dd_test':bte[1],'hedged_cagr_test':hte[0],'hedged_dd_test':hte[1],
          'hedged_sharpe_test':hte[2],'switches_test':nte})
    hedge_df=pd.DataFrame(hedge_rows)
    hedge_df['score']=(hedge_df.hedged_dd_train-hedge_df.baseline_dd_train)+(hedge_df.hedged_cagr_train-hedge_df.baseline_cagr_train)*.5
    hedge_best=hedge_df.sort_values('score',ascending=False).groupby(['long','inverse']).head(3)
    swing_best.to_csv('scratch/hk_inverse_swing_results.csv',index=False)
    orb_best.to_csv('scratch/hk_inverse_orb_results.csv',index=False)
    hedge_best.to_csv('scratch/hk_inverse_hedge_results.csv',index=False)
    print('\nSWING\n',swing_best.to_string(index=False));print('\nORB\n',orb_best.to_string(index=False));print('\nHEDGE\n',hedge_best.to_string(index=False))

if __name__=='__main__':main()
