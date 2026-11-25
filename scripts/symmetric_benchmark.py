"""Signed symmetric-cell observation benchmark; effective ASR, not interface identification."""
import argparse, hashlib, io, json, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

EXPECTED='6648d1faef5a26d5f0c77c41cdaf90274798081d460cffd83d5e9f6b4ac4b0fc'
GROUPS=(('Pristine',0),('2 OPA',5),('2 Li-OPA',10))

def condition(j):
    # Representative BV scale, not measured j0. Normalized columns remove unit scaling.
    x=np.column_stack((j,np.arcsinh(j)))
    x=x/np.linalg.norm(x,axis=0)
    s=np.linalg.svd(x,compute_uv=False)
    return float(s[-1]/s[0])

def predict(kind,p,t):
    if kind=='constant': return np.full_like(t,p[0],dtype=float)
    # Positive endpoints and convex interpolation ensure passive effective resistance.
    return p[1]+(p[0]-p[1])*np.exp(-t/p[2])

def fit(kind,t,r):
    if kind=='constant': return np.array([r.mean()])
    # fixed exploratory bounds, multiple deterministic starts; t in hours.
    fits=[least_squares(lambda p:predict(kind,p,t)-r,[r[0],r[-1],tau],bounds=([0,0,1],[np.inf,np.inf,1000])) for tau in (2,10,50,200,900)]
    fits=[f for f in fits if f.success and np.isfinite(f.cost)]
    if not fits: raise RuntimeError('relaxation optimization failed')
    return min(fits,key=lambda f:f.cost).x

def analyze(data):
    if hashlib.sha256(data).hexdigest()!=EXPECTED: raise ValueError('unexpected ASR export hash')
    raw=pd.read_csv(io.BytesIO(data),header=None,skiprows=4,na_values=['--'])
    rows=[];diag=[]
    for name,k in GROUPS:
        b=raw.iloc[:,k:k+4].apply(pd.to_numeric,errors='coerce');b.columns=['t','v','r','j'];b=b.dropna();b=b[b.j.abs()>1e-6].copy()
        if not np.isfinite(b.to_numpy()).all() or (b.r<0).any(): raise ValueError('invalid input')
        b['hour']=np.floor(b.t).astype(int)
        h=b.groupby('hour').r.median();tr=h[(h.index>=1)&(h.index<30)];te=h[(h.index>=30)&(h.index<50)]
        if len(tr)!=29 or len(te)!=20: raise ValueError('incomplete bins')
        j=b.j.to_numpy();diag.append(dict(group=name,n=len(b),abs_j_min=float(abs(j).min()),abs_j_max=float(abs(j).max()),sign_agreement=float(np.mean(b.v*j>0)),bv_singular_ratio=condition(j)))
        for kind in ('constant','relaxation'):
            p=fit(kind,tr.index.to_numpy(float),tr.to_numpy())
            for lo,hi in ((30,50),(50,100),(100,140),(140,400)):
                htest=h[(h.index>=lo)&(h.index<hi)]
                if not len(htest):continue
                # Exclude incomplete last hour by requiring floor(last timestamp) > hour.
                htest=htest[htest.index<int(b.t.max())]
                if not len(htest):continue
                pred=predict(kind,p,htest.index.to_numpy(float));err=htest.to_numpy()-pred
                a=b[b.hour.isin(htest.index)].copy()
                a['sq']=(a.v-2*a.j*predict(kind,p,a.hour.to_numpy(float)))**2
                rows.append(dict(group=name,model=kind,start=lo,end=hi,hours=len(htest),parameters=p.tolist(),asr_rmse=float(np.sqrt(np.mean(err**2))),voltage_rmse_mv=float(np.sqrt(a.groupby('hour').sq.mean().mean()))))
    return dict(diagnostics=diag,metrics=rows)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('zip');parser.add_argument('--out',required=True);a=parser.parse_args()
    with zipfile.ZipFile(a.zip) as z: result=analyze(z.read('liopa/sp_asr.csv'))
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n')
