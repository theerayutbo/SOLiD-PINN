"""Reproduce the exploratory LiOPA ASR time-block comparison from the evidence ZIP."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd
from scipy.stats import linregress

EXPECTED = "6648d1faef5a26d5f0c77c41cdaf90274798081d460cffd83d5e9f6b4ac4b0fc"
GROUPS = (("Pristine",0),("2 OPA",5),("2 Li-OPA",10))

def analyze(data):
    if hashlib.sha256(data).hexdigest()!=EXPECTED:
        raise ValueError("unexpected ASR export hash")
    raw=pd.read_csv(io.BytesIO(data),header=None,skiprows=4,na_values=["--"])
    results=[]
    for name,k in GROUPS:
        a=raw.iloc[:,k:k+4].apply(pd.to_numeric,errors="coerce")
        a.columns=["t","v","asr","j"]
        b=a.dropna()
        b=b[b.j.abs()>1e-6].copy()
        if not np.isfinite(b.to_numpy()).all() or (b.asr<0).any():
            raise ValueError("invalid ASR observations")
        e=b.asr-b.v.abs()/(2*b.j.abs())
        b["hour"]=np.floor(b.t).astype(int)
        h=b.groupby("hour").asr.median()
        tr=h[(h.index>=1)&(h.index<30)]
        te=h[(h.index>=30)&(h.index<50)]
        if len(tr)!=29 or len(te)!=20:
            raise ValueError("missing expected hourly bins")
        c=tr.mean()
        slope,intercept,*_=linregress(tr.index,tr)
        p0=np.full(len(te),c)
        p1=intercept+slope*te.index
        results.append(dict(group=name,n=len(b),duration=float(b.t.max()),
            asr_median=float(b.asr.median()),max_identity_error=float(e.abs().max()),
            common_median=float(b.loc[b.t<50,"asr"].median()),
            train_hours=len(tr),test_hours=len(te),constant_asr=float(c),
            linear_slope=float(slope),linear_intercept=float(intercept),
            constant_rmse=float(np.sqrt(np.mean((te-p0)**2))),
            linear_rmse=float(np.sqrt(np.mean((te-p1)**2)))))
    return results

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence_zip")
    p.add_argument("--out",required=True)
    a=p.parse_args()
    with zipfile.ZipFile(a.evidence_zip) as z:
        data=z.read("liopa/sp_asr.csv")
    rows=analyze(data)
    Path(a.out).write_text(json.dumps(rows,indent=2)+"\n")
