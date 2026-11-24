"""Audit verified reference timing and C20 voltage metrics, no fitting."""
import argparse, hashlib, json, platform
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
import paper_reproduction as paper
from run_v073_convergence import load_ocv, HASHES, PARAMS
from run_v073_inventory_audit import ACTIVE_FRACTION, WINDOW, mapped_ocv

REF_HASHES={20:'4b9e0f2688a8db78285f8b7b5ad67db4c28f0479196c2f1c5b3bcdf46a5b4c33',10:'04774e5dc719d75e3f7bd0d3f0447b2b564634e2979ed94451299b143336bb49',5:'bd127f24c6104a70c4756b654b5cf11eab2bc0d7d93708ae7cb8e098326f90ed'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(path,rate):
    if sha(path)!=REF_HASHES[rate]:raise ValueError('reference hash mismatch')
    t,v=pd.read_csv(path).to_numpy(float).T
    if not np.isfinite(t).all() or not np.isfinite(v).all() or np.any(np.diff(t)<0):raise ValueError('invalid reference')
    k=int(v.argmax()); f=165/rate
    if not 0<k<len(t)-1:raise ValueError('invalid peak')
    # Conditional interval: actual reversal lies between maximum observed voltage and next observation.
    lo,hi=t[k],t[k+1]
    excess_min=f*(t[-1]+t[0]-2*hi)
    excess_max=f*(t[-1]+t[0]-2*lo)
    return dict(rate=rate,points=len(t),duplicate_timestamps=int(np.sum(np.diff(t)==0)),peak_voltage_v=v[k],switch_gap_h=hi-lo,charge_h=lo-t[0],discharge_h=t[-1]-lo,charge_mah_g=f*(lo-t[0]),discharge_mah_g=f*(t[-1]-lo),excess_min_mah_g=excess_min,excess_max_mah_g=excess_max,initial_theta_upper_bound_at_mass_inventory=1-excess_min/paper.inventory(ACTIVE_FRACTION),last_voltage_v=v[-1])

def run(input_dir,ocv_dir,out):
    base=Path(input_dir);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    u=load_ocv(ocv_dir)
    audit_rows=[audit(base/f'Ref_data_at_C{rate}.csv',rate) for rate in (20,10,5)]
    pd.DataFrame(audit_rows).to_csv(out/'reference_audit.csv',index=False)
    ref=paper.split_ref(base/'Ref_data_at_C20.csv')
    cases=[('historical',PARAMS[0],1.,1.),('mass_nominal',ACTIVE_FRACTION,WINDOW,1.),('mass_nominal_collaborator_initial',ACTIVE_FRACTION,WINDOW,.9818)]
    rows=[]
    for name,eps,width,theta in cases:
        m=paper.PaperFEM(mapped_ocv(u,width),eps,PARAMS[1],PARAMS[2],nx=8,nr=20)
        c=np.full(m.shape,theta)
        for stage in ('charge','discharge'):
            row=dict(case=name,stage=stage,eps=eps,window=width,initial_theta=theta)
            try:
                trace,c,d=m.stage(stage,20,c)
                if not np.isfinite(c).all() or c.min() < -1e-5 or c.max()>1+1e-5:raise RuntimeError('terminal occupancy out of bounds')
                row.update(d,**paper.metrics(trace,ref[stage],20),status='complete')
                row['capacity_error_pct']=100*(row['capacity_mah_g']/row['reference_capacity_mah_g']-1)
                row['capacity_gate']=bool(abs(row['capacity_error_pct'])<=3.5 and row['termination']=='voltage')
            except (ValueError,RuntimeError,ArithmeticError) as e:row.update(status='failure',error=str(e))
            rows.append(row);pd.DataFrame(rows).to_csv(out/'c20_metrics.csv',index=False)
            if row['status']=='failure':break
    manifest=dict(purpose='reference audit and fixed structural diagnostic, no fit',reference_sha256=REF_HASHES,ocv_sha256=HASHES,source_sha256={p.name:sha(p) for p in [Path(__file__),Path(paper.__file__),Path(__file__).with_name('run_v073_convergence.py'),Path(__file__).with_name('run_v073_inventory_audit.py')]},python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,nx=8,nr=20,case_definitions=cases,phase=PARAMS[1],j0=PARAMS[2],rate=20,max_step_s=120,rtol=1e-7,atol=1e-9,output_step_s=30,reference_convention='maximum observed voltage split; duplicate timestamps averaged within stage; RMSE common interval after first 60 s; no extrapolation',switch_interval='conditional on reversal between maximum observation and next observation; not verified by current data')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return rows
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input_dir');p.add_argument('ocv_dir');p.add_argument('--outdir',required=True);a=p.parse_args();rows=run(a.input_dir,a.ocv_dir,a.outdir);raise SystemExit(0 if len(rows)==6 and all(r['status']=='complete' for r in rows) else 1)
