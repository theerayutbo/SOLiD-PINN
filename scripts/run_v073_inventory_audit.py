"""C20 structural inventory/SOC diagnostic; no fitting or reference traces."""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
import paper_reproduction as paper
from run_v073_convergence import load_ocv, HASHES, PARAMS

# Nominal stoichiometric LiNi0.6Mn0.2Co0.2O2, one Li site per formula unit.
MOLAR_MASS = (6.94 + .6*58.6934 + .2*54.938044 + .2*58.933194 + 2*15.999)/1000
LOADING_KG_M2 = paper.M / 1000 / paper.A
DENSITY = paper.C*MOLAR_MASS
ACTIVE_FRACTION = LOADING_KG_M2/(DENSITY*paper.L)
FULL_CAPACITY = paper.F/(3600*MOLAR_MASS)
WINDOW = 165/FULL_CAPACITY
REF = {'charge':143.50875,'discharge':148.60725}  # archived v0.7.2 duration-derived capacities only


def mapped_ocv(ocv, width):
    if not 0 < width <= 1:
        raise ValueError('invalid width')
    return {s:(lambda x, f=f: f(np.clip(np.asarray(x)/width,0,1))) for s,f in ocv.items()}


def run(ocv_dir, outdir):
    u = load_ocv(ocv_dir)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    # One coupled structural change: mass-consistent fraction + nominal SOC window.
    # Keep provisional phase correction and j0 fixed. Mapping clamps outside normalized range;
    # the physical lattice remains bounded [0,1]. This is not a measured window.
    cases = [('historical',PARAMS[0],1.),('mass_consistent_nominal_window',ACTIVE_FRACTION,WINDOW)]
    rows = []
    for label, eps, width in cases:
        m = paper.PaperFEM(mapped_ocv(u,width),eps,PARAMS[1],PARAMS[2],nx=8,nr=20)
        state = None
        for stage in ('charge','discharge'):
            t0=time.monotonic()
            row=dict(case=label,stage=stage,eps=eps,window=width,nx=8,nr=20)
            try:
                trace,state,d=m.stage(stage,20,state)
                if not np.isfinite(state).all() or state.min() < -1e-5 or state.max() > 1+1e-5:
                    raise RuntimeError('invalid terminal state')
                row.update(d,cutoff_h=float(trace.time_h.iloc[-1]),state_min=float(state.min()),state_max=float(state.max()),status='complete')
                row['reference_capacity_mah_g']=REF[stage]
                row['capacity_error_pct']=100*(d['capacity_mah_g']/REF[stage]-1)
            except (ValueError,RuntimeError,ArithmeticError) as e:
                row.update(status='failure',error=str(e))
            row['runtime_s']=time.monotonic()-t0
            rows.append(row)
            pd.DataFrame(rows).to_csv(out/'metrics.csv',index=False)
            print(row,flush=True)
            if row['status']=='failure': break
    files=[__file__,paper.__file__,str(Path(__file__).with_name('run_v073_convergence.py'))]
    manifest=dict(purpose='conditional structural diagnostic; no fitting; archived capacities only',input_sha256=HASHES,source_sha256={Path(f).name:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files},python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,pandas=pd.__version__,molar_mass_kg_mol=MOLAR_MASS,loading_kg_m2=LOADING_KG_M2,density_kg_m3=DENSITY,active_fraction=ACTIVE_FRACTION,one_li_capacity_mah_g=FULL_CAPACITY,nominal_window=WINDOW,phase=PARAMS[1],j0=PARAMS[2],rate=20,nx=8,nr=20,rtol=1e-7,atol=1e-9,max_step_s=120,output_step_s=30,reference=REF,reference_scope='archived duration-derived collaborator capacities, not raw curves')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('ocv_dir');p.add_argument('--outdir',required=True)
    a=p.parse_args();rows=run(a.ocv_dir,a.outdir)
    raise SystemExit(0 if len(rows)==4 and all(r['status']=='complete' for r in rows) else 1)
