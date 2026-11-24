"""C/20 numerical convergence only; verified private OCV, no reference fitting."""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
from scipy.interpolate import PchipInterpolator
import paper_reproduction as paper

HASHES = {
    'charge': '6f4526609a656ee320634d38975c47ea71b36dec08cbfc761d5e4a4469ef4457',
    'discharge': '0ba51db95aca0d9334854251bd14e80104e6fa4afeab34803a99cc5f5bf65d6c',
}
PARAMS = (paper.Q*3600/(paper.F*paper.C*paper.L*paper.A), .131, .0566011934)
STAGES = ('charge', 'discharge')
PLAN = (
    ('mesh_4x10', 4, 10, 120, 1e-7, 1e-9),
    ('mesh_8x20', 8, 20, 120, 1e-7, 1e-9),
    ('mesh_16x40', 16, 40, 120, 1e-7, 1e-9),
    ('step_60', 16, 40, 60, 1e-7, 1e-9),
    ('step_30', 16, 40, 30, 1e-7, 1e-9),
    ('tight_tol', 16, 40, 30, 1e-8, 1e-10),
)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_ocv(folder):
    u = {}
    for stage, expected in HASHES.items():
        p = Path(folder)/f'ocv_{stage}_digitized.csv'
        if sha(p) != expected:
            raise ValueError(f'OCV hash mismatch: {p.name}')
        a = pd.read_csv(p).to_numpy(float)
        if a.ndim != 2 or a.shape[1] != 2 or not np.isfinite(a).all() or np.any(np.diff(a[:,0]) <= 0):
            raise ValueError(f'Invalid OCV: {p.name}')
        u[stage] = PchipInterpolator(a[:,0], a[:,1])
    return u

def compare(old, new, old_trace, new_trace):
    end = min(old_trace.time_h.iloc[-1], new_trace.time_h.iloc[-1])
    start = max(old_trace.time_h.iloc[0], new_trace.time_h.iloc[0])
    if end <= start or old['capacity_mah_g'] <= 0 or old['cutoff_h'] <= 0:
        raise ValueError('Invalid common interval or denominator')
    t = np.linspace(start, end, 2001)
    v = np.interp(t, new_trace.time_h, new_trace.voltage_v) - np.interp(t, old_trace.time_h, old_trace.voltage_v)
    cap = 100*abs(new['capacity_mah_g']/old['capacity_mah_g']-1)
    cutoff = 100*abs(new['cutoff_h']/old['cutoff_h']-1)
    rmse = 1000*np.sqrt(np.mean(v*v))
    physical = all(r['termination']=='voltage' and r['mass_error_mah_g'] <= 1e-6 and r['state_min'] >= -1e-5 and r['state_max'] <= 1+1e-5 for r in (old,new))
    return dict(capacity_change_pct=cap, cutoff_change_pct=cutoff, voltage_rmse_mv=rmse,
                common_time_h=end-start, coverage_old_pct=100*(end-start)/old['cutoff_h'],
                coverage_new_pct=100*(end-start)/new['cutoff_h'],
                passed=bool(physical and cap<=.5 and cutoff<=.5 and rmse<=1))

def run(ocv_dir, outdir, count=len(PLAN)):
    if not 1 <= count <= len(PLAN):
        raise ValueError('count outside plan')
    u = load_ocv(ocv_dir)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = dict(schema=1, purpose='numerical convergence; no reference data or fitting',
                    input_sha256=HASHES, source_sha256={Path(p).name:sha(p) for p in (__file__,paper.__file__)},
                    python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, pandas=pd.__version__,
                    case='historical_kinetics', params=PARAMS, rate=20, output_step_s=30, plan=PLAN[:count],
                    state_check='terminal state only', comparison='2001 common-time points, no extrapolation')
    identity = hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()[:20]
    out = out/identity
    out.mkdir(exist_ok=True)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    rows, comparisons, previous = [], [], {}
    for label,nx,nr,step,rtol,atol in PLAN[:count]:
        model = paper.PaperFEM(u,*PARAMS,nx=nx,nr=nr)
        state = None
        current = {}
        for stage in STAGES:
            record = dict(run=label,nx=nx,nr=nr,max_step_s=step,rtol=rtol,atol=atol,stage=stage)
            begin = time.monotonic()
            try:
                trace,state,d = model.stage(stage,20,state,max_step=step,rtol=rtol,atol=atol,output_step=30)
                if state.shape!=model.shape or not np.isfinite(state).all() or not np.isfinite(trace.to_numpy()).all():
                    raise RuntimeError('invalid numerical state or trace')
                record.update(d, status='complete', cutoff_h=float(trace.time_h.iloc[-1]),state_min=float(state.min()),state_max=float(state.max()),runtime_s=time.monotonic()-begin)
                if stage in previous:
                    prev, prev_trace = previous[stage]
                    comparisons.append(dict(coarse=prev['run'],fine=label,stage=stage,**compare(prev,record,prev_trace,trace)))
                current[stage] = (record,trace)
            except (ValueError,RuntimeError,ArithmeticError) as exc:
                record.update(status='failure',error=str(exc),runtime_s=time.monotonic()-begin)
            rows.append(record)
            pd.DataFrame(rows).to_csv(out/'metrics.csv',index=False)
            pd.DataFrame(comparisons).to_csv(out/'comparisons.csv',index=False)
            print(json.dumps(record),flush=True)
            if record['status']=='failure':
                break
        previous = current if len(current)==2 else {}
    final_pairs = [('mesh_8x20','mesh_16x40'),('step_60','step_30'),('step_30','tight_tol')]
    expected = {(a,b,s) for a,b in final_pairs for s in STAGES}
    passed = {(c['coarse'],c['fine'],c['stage']) for c in comparisons if c['passed']}
    status = 'partial' if count<len(PLAN) else ('pass' if len(rows)==12 and all(r['status']=='complete' for r in rows) and expected<=passed else 'fail')
    result = dict(status=status,completed=sum(r['status']=='complete' for r in rows),expected=2*count,gate='numerical only; C/20 model selection not established')
    (out/'status.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RUN_DIR',out,flush=True)
    print('GATE_A',json.dumps(result),flush=True)
    return out,result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('ocv_dir');p.add_argument('--outdir',required=True);p.add_argument('--count',type=int,default=len(PLAN))
    a=p.parse_args();_,status=run(a.ocv_dir,a.outdir,a.count)
    raise SystemExit(0 if status['status'] in ('pass','partial') else 1)
