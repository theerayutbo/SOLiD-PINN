"""Terminal ASR falsification on authorized local traces, not a coupled solver.
C20-only fit, frozen C10/C5 evaluation; higher-rate diagnostic estimates are not fits used in prediction.
"""
import numpy as np
import pandas as pd
from pathlib import Path


def fit_nonnegative_asr(error_v, current_density):
    e, j = np.asarray(error_v, float), np.asarray(current_density, float)
    if e.shape != j.shape or not e.size or not np.isfinite(e).all() or not np.isfinite(j).all() or np.dot(j,j) <= 0:
        raise ValueError('invalid residual/current arrays')
    unconstrained = float(np.dot(e,j)/np.dot(j,j))
    return max(0., unconstrained), unconstrained


def load_sim(root, rate):
    if rate == 20:
        t,v=np.loadtxt(root/'V_vs_t_C20_sim.txt',comments='%').T
        events=np.flatnonzero(abs(np.diff(t))<1e-8)
        if len(events)!=1: raise ValueError('ambiguous C20 switching event')
        k=int(events[0]);i=np.r_[np.full(k+1,-.000233475/rate),np.full(len(t)-k-1,.000233475/rate)]
    else:
        a=np.loadtxt(root/f'C{rate}_data.txt',comments='%')
        if (a.shape[1]-1)%3: raise ValueError('invalid triples')
        triples=a[:,1:].reshape(len(a),-1,3)
        if not np.allclose(triples,triples[:1],rtol=0,atol=1e-10): raise ValueError('non-global export')
        t,v,i=triples[0].T;i=-i
        events=np.flatnonzero(np.diff(np.sign(i)))
        if len(events)!=1: raise ValueError('ambiguous switch')
        k=int(events[0])
    if not np.isfinite(np.c_[t,v,i]).all() or i[0]>=0 or i[-1]<=0 or abs(t[k+1]-t[k])>1e-8: raise ValueError('bad simulation protocol')
    return t,v,i,k


def prepare(root,rate,n=1000):
    t,v,i,k=load_sim(root,rate)
    ref=pd.read_csv(root/f'Ref_data_at_C{rate}.csv').to_numpy(float)
    if not np.isfinite(ref).all() or np.any(np.diff(ref[:,0])<0): raise ValueError('bad reference time')
    j=int(np.argmax(ref[:,1]));rows=[]
    for stage,sl,rs in [('charge',slice(None,k+1),slice(None,j+1)),('discharge',slice(k+1,None),slice(j+1,None))]:
        tm=t[sl]-t[sl][0];vm=v[sl];tr=ref[rs,0]-(ref[0,0] if stage=='charge' else ref[j,0]);vr=ref[rs,1]
        d=pd.DataFrame({'t':tr,'v':vr}).groupby('t',as_index=False).mean();tr=d.t.to_numpy();vr=d.v.to_numpy()
        start=max(1/60,tm[0],tr[0]);end=min(tm[-1],tr[-1])
        if end<=start or np.any(np.diff(tm)<=0):raise ValueError('invalid common interval')
        q=np.linspace(start,end,n);e=np.interp(q,tm,vm)-np.interp(q,tr,vr);J=i[sl][0]/2.83e-5
        if not np.allclose(i[sl],i[sl][0],rtol=1e-6,atol=1e-12):raise ValueError('nonconstant stage current')
        rows.append((stage,e,np.full(n,J),start,end,float(tr[-1])))
    return rows


def diagnose(root):
    root=Path(root); train=prepare(root,20); R,raw=fit_nonnegative_asr(np.concatenate([r[1] for r in train]),np.concatenate([r[2] for r in train]))
    output=[]
    for rate in (20,10,5):
        for stage,e,j,start,end,duration in (train if rate==20 else prepare(root,rate)):
            _, diagnostic=fit_nonnegative_asr(e,j)
            output.append(dict(rate=rate,stage=stage,baseline_rmse_mv=1000*np.sqrt(np.mean(e**2)),frozen_rmse_mv=1000*np.sqrt(np.mean((e-j*R)**2)),bias_mv=1000*e.mean(),diagnostic_unconstrained_asr_ohm_m2=diagnostic,fit_C20_asr_ohm_m2=R,fit_C20_unconstrained_ohm_m2=raw,start_h=start,end_h=end,reference_duration_h=duration))
    return pd.DataFrame(output)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input_dir');p.add_argument('--out',default='outputs/v07_asr_diagnostic.csv');a=p.parse_args()
    d=diagnose(a.input_dir);out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);d.to_csv(out,index=False);print(d.to_string(index=False))
