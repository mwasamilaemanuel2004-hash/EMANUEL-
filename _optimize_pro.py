"""Profitable scalper optimizer - Gen Pro."""
import json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

FEE = 0.001
MAX_BARS = 10000

def load_data(tf):
    cache = ROOT / f"_cache_{tf}.csv"
    if cache.exists():
        df = pd.read_csv(cache, index_col=0, parse_dates=True)
        df.index = pd.to_datetime(df.index, utc=True) if df.index.tz is None else df.index
        for col in ("open","high","low","close","volume"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.dropna()
    import requests
    url = "https://api.binance.com/api/v3/klines"
    rows = []; end_time = None
    while len(rows) < MAX_BARS:
        params = {"symbol":"BTCUSDT","interval":tf,"limit":1000}
        if end_time: params["endTime"] = end_time
        r = requests.get(url, params=params, timeout=20); r.raise_for_status()
        batch = r.json()
        if not batch: break
        rows = batch + rows
        nxt = int(batch[0][0]) - 1
        if end_time == nxt: break
        end_time = nxt
        if len(batch) < 1000: break
        time.sleep(0.05)
    rows = rows[-MAX_BARS:]
    df = pd.DataFrame(rows, columns=["ot","open","high","low","close","volume","ct","qv","tr","tbv","tbqv","ign"])
    df.index = pd.to_datetime(df.pop("ot"), unit="ms", utc=True)
    for col in ("open","high","low","close","volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open","high","low","close","volume"])
    df.to_csv(cache)
    return df

def precompute(df):
    c=df["close"].astype(float); h=df["high"].astype(float); l=df["low"].astype(float)
    o=df["open"].astype(float); v=df["volume"].astype(float); prev=c.shift(1)
    tr=pd.concat([h-l,(h-prev).abs(),(l-prev).abs()],axis=1).max(axis=1)
    atr=tr.rolling(14).mean()
    e20=c.ewm(span=20,adjust=False).mean(); e50=c.ewm(span=50,adjust=False).mean()
    e200=c.ewm(span=200,adjust=False).mean(); vm=v.rolling(20).mean()
    cr=(h-l).clip(lower=1e-12); body=c-o; bp=body.abs()/cr
    uw=(h-c.clip(lower=o))/cr; lw=(c.clip(upper=h)-o.clip(upper=h))/cr
    return {"c":c.to_numpy(),"h":h.to_numpy(),"l":l.to_numpy(),"o":o.to_numpy(),
            "v":v.to_numpy(),"atr":atr.to_numpy(),"e20":e20.to_numpy(),"e50":e50.to_numpy(),
            "e200":e200.to_numpy(),"vm":vm.to_numpy(),"body":body.to_numpy(),
            "bp":bp.to_numpy(),"uw":uw.to_numpy(),"lw":lw.to_numpy(),
            "hr":df.index.hour.to_numpy() if hasattr(df.index,'hour') else np.zeros(len(df)),
            "n":len(df)}

def sim(feat, cfg):
    n=feat["n"]; c=feat["c"]; h=feat["h"]; l=feat["l"]; v=feat["v"]
    atr=feat["atr"]; e20=feat["e20"]; e50=feat["e50"]; e200=feat["e200"]
    vm=feat["vm"]; body=feat["body"]; bp=feat["bp"]; uw=feat["uw"]; lw=feat["lw"]; hr=feat["hr"]
    horizon=cfg["horizon"]; rr=cfg["rr"]; sm=cfg["sm"]
    tfilt=bool(cfg.get("tfilt",True)); vfilt=bool(cfg.get("vfilt",True)); vmul=cfg.get("vmul",1.2)
    mbp=cfg.get("mbp",0.3); ptp=cfg.get("ptp",0.002); cd=cfg.get("cd",0)
    md=cfg.get("md",0.5); tod=bool(cfg.get("tod",False))
    outcomes=[]; nloss=0; last_i=-999; eq=0.0; peq=0.0
    for i in range(60,n-horizon):
        if cd>0 and (i-last_i)<cd: continue
        if nloss>=3: continue
        a=atr[i]
        if a<=0 or np.isnan(a): continue
        cl=c[i]; sw=a*sm
        tu = (bool(cl>e200) and bool(e50>e200)) if tfilt else True
        td = (bool(cl<e200) and bool(e50<e200)) if tfilt else True
        if vfilt and vm[i]>0 and v[i]<vmul*vm[i]: continue
        if a/cl>0.02: continue
        if tod and 0<=int(hr[i])<7: continue
        side=None
        if tu:
            td2=abs(cl-e20[i])/cl
            if td2<=ptp or l[i]<=e20[i]:
                if body[i]>0 and bp[i]>=mbp and lw[i]>=0.2:
                    side="BUY"
        if td and side is None:
            td2=abs(cl-e20[i])/cl
            if td2<=ptp or h[i]>=e20[i]:
                if body[i]<0 and bp[i]>=mbp and uw[i]>=0.2:
                    side="SELL"
        if side is None: continue
        entry=cl
        if side=="BUY": sl=entry-sw; tp=entry+sw*rr
        else: sl=entry+sw; tp=entry-sw*rr
        risk=abs(entry-sl)
        if risk<=0: continue
        fh=h[i+1:i+1+horizon]; fl=l[i+1:i+1+horizon]
        if side=="BUY": sh=fl<=sl; tp2=fh>=tp
        else: sh=fh>=sl; tp2=fl<=tp
        si=np.argmax(sh) if sh.any() else horizon
        ti=np.argmax(tp2) if tp2.any() else horizon
        if sh.any() and (si<=ti or not tp2.any()):
            if tp2.any() and ti<si: exit_p=tp; val=rr
            else: exit_p=sl; val=-1.0
        elif tp2.any(): exit_p=tp; val=rr
        else: exit_p=c[min(i+horizon,n-1)]; val=(exit_p-entry)/risk if side=="BUY" else (entry-exit_p)/risk
        fee=(entry+exit_p)*FEE/risk; val-=fee
        outcomes.append(val); last_i=i
        if val>0: nloss=0
        else: nloss+=1
        eq+=val; peq=max(peq,eq)
        if peq>0 and (peq-eq)/peq>md: break
    if not outcomes: return {"trades":0,"pf":0,"exp":-999,"dd":999,"wr":0}
    wins=[x for x in outcomes if x>0]; losses=[x for x in outcomes if x<=0]
    eqc=np.cumsum(outcomes); pk=np.maximum.accumulate(eqc); dd=float((pk-eqc).max())
    return {"trades":len(outcomes),"pf":round(sum(wins)/abs(sum(losses)),3) if losses and sum(losses)!=0 else 999,
            "exp":round(sum(outcomes)/len(outcomes),4),"dd":round(dd,3),
            "wr":round(len(wins)/len(outcomes)*100,2)}


def main():
    results=[]
    for tf in ("1h",):
        print(f"Loading {tf}...")
        df=load_data(tf); feat=precompute(df)
        print(f"  {tf}: {feat['n']} bars")
        pg={"horizon":[12,18,24,36,48],"rr":[2.0,2.5,3.0,3.5,4.0],"sm":[1.0,1.5,2.0,2.5,3.0],
            "tfilt":[True,False],"vfilt":[True],"vmul":[1.0,1.2,1.5],"mbp":[0.2,0.3,0.4,0.5],
            "ptp":[0.001,0.002,0.003,0.005],"cd":[0,3,6],"md":[0.5],"tod":[True,False]}
        np.random.seed(42); n_samp=3000
        keys=list(pg.keys())
        cfgs=[{k:np.random.choice(pg[k]) for k in keys} for _ in range(n_samp)]
        bexp=-999; pcount=0
        for i,cfg in enumerate(cfgs):
            r=sim(feat,cfg); r["tf"]=tf; r["cfg"]=cfg; results.append(r)
            if r["exp"]>0: pcount+=1
            if r["exp"]>bexp:
                bexp=r["exp"]
                print(f"  [{i+1}/{n_samp}] BEST: exp={r['exp']:.4f} pf={r['pf']} wr={r['wr']}% t={r['trades']} dd={r['dd']}")
        print(f"\n{tf}: {pcount}/{n_samp} profitable")
        best=max(results,key=lambda x:x["exp"])
        print(f"  Best: exp={best['exp']} pf={best['pf']} wr={best['wr']}% t={best['trades']}")
        print(f"  Cfg: {best['cfg']}")
    with open(ROOT/"_pro_sweep_results.json","w") as f: json.dump(results,f,indent=2)
    prof=[r for r in results if r["exp"]>0]; prof.sort(key=lambda x:x["exp"],reverse=True)
    print(f"\nTop {min(10,len(prof))} profitable:")
    for r in prof[:10]:
        print(f"  exp={r['exp']:.4f} pf={r['pf']} wr={r['wr']}% t={r['trades']} tf={r['tf']}")
        print(f"    {r['cfg']}")

if __name__=="__main__":
    main()
