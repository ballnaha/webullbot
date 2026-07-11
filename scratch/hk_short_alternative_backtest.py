"""Walk-forward tests for three alternative HK inverse-ETF strategies."""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import yfinance as yf

FEE, SLIP = .0012, .0005
PAIRS = {"2800.HK":"7500.HK", "3033.HK":"7552.HK"}


def stats(eq, trades, wins, ppy=252):
    e=pd.Series(eq,dtype=float); years=max(len(e)/ppy,1/ppy)
    r=e.pct_change().dropna(); sh=np.sqrt(ppy)*r.mean()/r.std() if r.std()>0 else 0
    return e.iloc[-1]**(1/years)-1,(e/e.cummax()-1).min(),sh,trades,wins/trades if trades else np.nan


def gap_test(u,x,gap_min,confirm_bars,vol_factor,start_day=0,end_day=None):
    idx=u.index.intersection(x.index);u,x=u.loc[idx],x.loc[idx]
    days=sorted(set(idx.date)); end_day=len(days) if end_day is None else end_day
    cash=1.;eq=[];trades=wins=0;prev_close=None
    for di,day in enumerate(days):
        loc=np.flatnonzero(idx.date==day);ud,xd=u.iloc[loc],x.iloc[loc]
        if len(loc)<25:continue
        if prev_close is None:prev_close=float(ud.close.iloc[-1]);continue
        gap=float(ud.open.iloc[0])/prev_close-1;prev_close=float(ud.close.iloc[-1])
        if di<start_day:continue
        if di>=end_day:break
        n=confirm_bars;typ=(ud.high+ud.low+ud.close)/3
        vwap=(typ*ud.volume).cumsum()/ud.volume.cumsum().replace(0,np.nan)
        avgvol=ud.volume.iloc[:n].mean()
        cond=(gap<=-gap_min and float(ud.close.iloc[n-1])<float(ud.open.iloc[0])
              and float(ud.close.iloc[n-1])<float(vwap.iloc[n-1])
              and float(ud.volume.iloc[:n].mean())>=avgvol*vol_factor)
        if cond and n<len(xd)-2:
            entry=float(xd.open.iloc[n])*(1+SLIP);exit_=float(xd.close.iloc[-2])*(1-SLIP)
            new=cash*(1-FEE)/entry*exit_*(1-FEE);wins+=new>cash;cash=new;trades+=1
        eq.append(cash)
    return stats(eq,trades,wins)


def crash_test(u,x,lookback,drop,regime,hold,sl,tp,start=0):
    idx=u.index.intersection(x.index);u,x=u.loc[idx],x.loc[idx]
    signal=(u.close.pct_change(lookback)<=-drop)&(u.close<u.close.rolling(regime).mean())
    cash=1.;units=0.;entry=0.;age=0;ev=0.;eq=[];trades=wins=0
    for i in range(max(1,start),len(idx)):
        o,h,l,c=(float(x.iloc[i][z]) for z in ('open','high','low','close'));out=None
        if units:
            age+=1
            if l<=entry*(1-sl):out=min(o,entry*(1-sl))
            elif h>=entry*(1+tp):out=max(o,entry*(1+tp))
            elif age>=hold:out=o
        if out is not None:
            proceeds=units*out*(1-SLIP)*(1-FEE);wins+=proceeds>ev;cash,units,trades=proceeds,0.,trades+1
        if not units and bool(signal.iloc[i-1]):
            entry=o*(1+SLIP);ev=cash;units=cash*(1-FEE)/entry;cash,age=0.,0
        eq.append(cash+units*c)
    return stats(eq,trades,wins)


def rotation(data,lookback,volwin,rebalance,start=0):
    idx=data['2800.HK'].index
    for s in data:idx=idx.intersection(data[s].index)
    d={s:data[s].loc[idx] for s in data};cash=1.;asset=None;units=0.;eq=[];trades=wins=0;ev=0.
    for i in range(max(lookback,volwin,start,1),len(idx)):
        if (i-start)%rebalance==0:
            scores={}
            for under in PAIRS:
                ret=float(d[under].close.iloc[i-1]/d[under].close.iloc[i-1-lookback]-1)
                vol=float(d[under].close.pct_change().iloc[:i].tail(volwin).std())
                scores[under]=ret/max(vol,1e-6)
            weakest=min(scores,key=scores.get);target=PAIRS[weakest] if scores[weakest]<0 else None
            if target!=asset:
                if asset:
                    px=float(d[asset].open.iloc[i])*(1-SLIP);proceeds=units*px*(1-FEE);wins+=proceeds>ev;cash,units,trades=proceeds,0.,trades+1
                asset=None
                if target:
                    px=float(d[target].open.iloc[i])*(1+SLIP);ev=cash;units=cash*(1-FEE)/px;cash=0.;asset=target
        value=cash+(units*float(d[asset].close.iloc[i]) if asset else 0);eq.append(value)
    return stats(eq,trades,wins)


def fetch(symbols,period,interval):
    raw=yf.download(symbols,period=period,interval=interval,auto_adjust=True,group_by='ticker',progress=False,threads=True);out={}
    for s in symbols:
        q=raw[s].rename(columns=str.lower).dropna(subset=['open','close']);out[s]=q[['open','high','low','close','volume']]
    return out


def main():
    cache=Path('scratch/yf_cache');cache.mkdir(exist_ok=True);yf.set_tz_cache_location(str(cache.resolve()))
    symbols=list(PAIRS)+list(PAIRS.values());daily=fetch(symbols,'max','1d');intra=fetch(symbols,'60d','5m')
    rows=[]
    # Intraday has a short sample: chronological half split by trading days.
    for under,inv in PAIRS.items():
      ndays=len(set(intra[under].index.date));split=ndays//2
      for gap,n,vf in itertools.product([.005,.01,.015],[3,6,12],[.8,1.]):
        tr=gap_test(intra[under],intra[inv],gap,n,vf,0,split);te=gap_test(intra[under],intra[inv],gap,n,vf,split)
        rows.append({'strategy':'gap','market':under,'params':f'gap{gap},bars{n},vf{vf}','train_cagr':tr[0],'train_dd':tr[1],'test_cagr':te[0],'test_dd':te[1],'test_sharpe':te[2],'test_trades':te[3],'win_rate':te[4]})
      common=daily[under].index.intersection(daily[inv].index);split=int(len(common)*.6)
      for lb,drop,regime,hold,sl,tp in itertools.product([2,3,5],[.03,.05,.07],[50,100,200],[1,2,3],[.03,.05],[.06,.10]):
        tr=crash_test(daily[under].loc[:common[split]],daily[inv].loc[:common[split]],lb,drop,regime,hold,sl,tp)
        te=crash_test(daily[under],daily[inv],lb,drop,regime,hold,sl,tp,split)
        rows.append({'strategy':'crash','market':under,'params':f'lb{lb},drop{drop},ma{regime},h{hold},sl{sl},tp{tp}','train_cagr':tr[0],'train_dd':tr[1],'test_cagr':te[0],'test_dd':te[1],'test_sharpe':te[2],'test_trades':te[3],'win_rate':te[4]})
    common=daily['2800.HK'].index.intersection(daily['3033.HK'].index).intersection(daily['7500.HK'].index).intersection(daily['7552.HK'].index);dd={s:daily[s].loc[common] for s in symbols};split=int(len(common)*.6)
    for lb,vw,reb in itertools.product([5,10,20],[10,20,40],[1,5,10]):
        tr=rotation({s:q.iloc[:split] for s,q in dd.items()},lb,vw,reb);te=rotation(dd,lb,vw,reb,split)
        rows.append({'strategy':'rotation','market':'HSI-vs-HSTECH','params':f'lb{lb},vol{vw},reb{reb}','train_cagr':tr[0],'train_dd':tr[1],'test_cagr':te[0],'test_dd':te[1],'test_sharpe':te[2],'test_trades':te[3],'win_rate':te[4]})
    result=pd.DataFrame(rows);result['score']=result.train_cagr+result.train_dd*.25
    result.loc[result.test_trades<3,'score']=-np.inf
    best=result.sort_values('score',ascending=False).groupby(['strategy','market']).head(8)
    result.to_csv('scratch/hk_short_alternative_all_results.csv',index=False);best.to_csv('scratch/hk_short_alternative_best_results.csv',index=False)
    print(best.to_string(index=False))

if __name__=='__main__':main()
