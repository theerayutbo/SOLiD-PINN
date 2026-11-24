"""Resumable private-data runner for the v0.7.2 paper reproduction.

Checkpoints are stage-boundary states, not serialized BDF integrator states.
A partially computed stage restarts; completed valid stages are reused.
Single writer per output directory. Never commit the private predictions.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import numpy as np
import pandas as pd
import scipy
from scipy.interpolate import PchipInterpolator
import paper_reproduction as paper

CASES = {
    "literal_0131": (.131, .131, 6.59173895),
    "inventory_derived": (paper.Q*3600/(paper.F*paper.C*paper.L*paper.A), .131, 6.59173895),
    "historical_kinetics": (paper.Q*3600/(paper.F*paper.C*paper.L*paper.A), .131, .0566011934),
}
RATES = (20, 10, 5)
STAGES = ("charge", "discharge")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def atomic(path, data):
    path = Path(path)
    tmp = path.with_name(path.name+".tmp")
    with tmp.open("wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def commit():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parent,
        text=True).strip()

def setup(base, outdir):
    base, outdir = Path(base), Path(outdir)
    inputs = [f"Ref_data_at_C{r}.csv" for r in RATES] + [
        f"SOLiD-PINN-OCV-Figure4/ocv_{s}_digitized.csv" for s in STAGES]
    info = dict(schema=1, revision=commit(), input_sha256={p:sha(base/p) for p in inputs},
                source_sha256={Path(p).name:sha(p) for p in (__file__,paper.__file__)},
                python=platform.python_version(), numpy=np.__version__,
                scipy=scipy.__version__, pandas=pd.__version__,
                cases={k:list(v) for k,v in CASES.items()}, rates=list(RATES),
                nx=4, nr=10, max_step_s=120, output_step_s=30,
                rtol=1e-7, atol=1e-9,
                note="Stage-local common time; private collaborator reference, not author-verified raw data")
    identity=json.dumps(info,sort_keys=True,separators=(",",":"))
    run=outdir/hashlib.sha256(identity.encode()).hexdigest()[:20]
    run.mkdir(parents=True,exist_ok=True)
    manifest=run/"manifest.json"
    if manifest.exists():
        if json.loads(manifest.read_text())!=info:
            raise ValueError("checkpoint manifest mismatch")
    else:
        atomic(manifest,(json.dumps(info,indent=2)+"\n").encode())
    u={}
    for stage in STAGES:
        a=pd.read_csv(base/f"SOLiD-PINN-OCV-Figure4/ocv_{stage}_digitized.csv").to_numpy(float)
        if a.ndim!=2 or a.shape[1]!=2 or not np.isfinite(a).all() or np.any(np.diff(a[:,0])<=0):
            raise ValueError("invalid OCV table: "+stage)
        u[stage]=PchipInterpolator(a[:,0],a[:,1])
    return run,u

def save_stage(path, row, state, pred):
    data=io.BytesIO()
    np.savez_compressed(data, state=np.asarray(state), time_h=pred.time_h.to_numpy(),
                        voltage_v=pred.voltage_v.to_numpy(), row=json.dumps(row,allow_nan=False))
    atomic(path,data.getvalue())

def load_stage(path, shape, case, rate, stage):
    with np.load(path,allow_pickle=False) as z:
        state=z["state"].copy(); t=z["time_h"].copy(); v=z["voltage_v"].copy()
        row=json.loads(z["row"].item())
    if (row["case"],row["rate"],row["stage"])!=(case,rate,stage):
        raise ValueError("checkpoint identity mismatch")
    if (state.shape!=shape or not np.isfinite(state).all() or
        state.min() < -1e-5 or state.max() > 1+1e-5 or
        t.ndim!=1 or v.shape!=t.shape or len(t)<2 or
        not np.isfinite(t).all() or not np.isfinite(v).all() or
        t[0]!=0 or np.any(np.diff(t)<=0) or
        row["termination"] not in ("voltage","occupancy")):
        raise ValueError("invalid checkpoint "+str(path))
    return row,state,pd.DataFrame(dict(time_h=t,voltage_v=v))

def summary(run):
    rows=[]
    for p in sorted(run.glob("*.npz")):
        with np.load(p,allow_pickle=False) as z:
            rows.append(json.loads(z["row"].item()))
    for p in sorted(run.glob("*.failure.json")):
        rows.append(json.loads(p.read_text()))
    if rows:
        atomic(run/"metrics.csv",pd.DataFrame(rows).to_csv(index=False).encode())
    return rows

def run_cases(base,outdir,cases=tuple(CASES),rates=RATES,limit=None):
    base=Path(base)
    run,u=setup(base,outdir)
    print("RUN_DIR",run,flush=True)
    completed=0
    for case in cases:
        eps,phase,j0=CASES[case]
        for rate in rates:
            m=paper.PaperFEM(u,eps,phase,j0)
            c=None
            ref=paper.split_ref(base/f"Ref_data_at_C{rate}.csv")
            for stage in STAGES:
                stem=f"{case}_{rate}_{stage}"
                path=run/(stem+".npz")
                failure=run/(stem+".failure.json")
                if path.exists():
                    row,c,pred=load_stage(path,m.shape,case,rate,stage)
                    failure.unlink(missing_ok=True)
                    print("RESUMED",stem,flush=True)
                else:
                    if limit is not None and completed>=limit:
                        summary(run)
                        return run
                    start=time.monotonic()
                    try:
                        pred,c,d=m.stage(stage,rate,c)
                        r=ref[stage]
                        if min(r.time_h.iloc[-1],pred.time_h.iloc[-1])<=max(r.time_h.iloc[0],1/60):
                            raise RuntimeError("no valid common time interval")
                        row=dict(case=case,rate=rate,stage=stage,eps=eps,phase=phase,j0=j0,
                                 **d,**paper.metrics(pred,r,rate),
                                 runtime_s=time.monotonic()-start,status="complete")
                        row["capacity_error_pct"]=100*(row["capacity_mah_g"]/row["reference_capacity_mah_g"]-1)
                        if row["termination"] not in ("voltage","occupancy"):
                            raise RuntimeError("no terminal event")
                        if not np.isfinite(c).all() or c.min() < -1e-5 or c.max() > 1+1e-5:
                            raise RuntimeError("unphysical state")
                        # Cast NumPy scalar values for JSON portability.
                        row={k:(v.item() if isinstance(v,np.generic) else v) for k,v in row.items()}
                        save_stage(path,row,c,pred)
                        failure.unlink(missing_ok=True)
                        completed+=1
                        print("SAVED",stem,row["capacity_error_pct"],flush=True)
                    except (RuntimeError,ValueError) as exc:
                        record=dict(case=case,rate=rate,stage=stage,status="failure",
                                    termination=str(exc),runtime_s=time.monotonic()-start)
                        atomic(failure,(json.dumps(record,indent=2)+"\n").encode())
                        print("FAILED",stem,exc,flush=True)
                        summary(run)
                        break
                # Recreate derived CSVs even after a crash after saving the state.
                atomic(run/(stem+".csv"),pred.to_csv(index=False).encode())
                summary(run)
    summary(run)
    return run

def execution_status(rows, cases, rates, limit=None):
    """Return coverage for the selected plan, not unrelated cached cases."""
    expected = {(case, rate, stage) for case in cases for rate in rates for stage in STAGES}
    complete = {(r["case"], r["rate"], r["stage"]) for r in rows
                if r["status"] == "complete"} & expected
    failed = {(r["case"], r["rate"], r["stage"]) for r in rows
              if r["status"] == "failure"} & expected
    missing = expected - complete
    status = ("failed" if failed or (missing and limit is None) else
              "partial" if missing else "complete")
    return dict(status=status, completed=len(complete), expected=len(expected),
                failed=sorted(failed), missing=sorted(missing))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_dir")
    p.add_argument("--outdir",required=True)
    p.add_argument("--case",action="append",choices=tuple(CASES))
    p.add_argument("--rate",action="append",type=int,choices=RATES)
    p.add_argument("--limit-new-stages",type=int)
    a=p.parse_args()
    if a.limit_new_stages is not None and a.limit_new_stages<1:
        p.error("limit must be positive")
    cases, rates = a.case or tuple(CASES), a.rate or RATES
    run = run_cases(a.input_dir,a.outdir,cases,rates,a.limit_new_stages)
    status = execution_status(summary(run), cases, rates, a.limit_new_stages)
    print("EXECUTION_STATUS", json.dumps(status), flush=True)
    return 1 if status["status"] == "failed" else 0

if __name__=="__main__":
    raise SystemExit(main())
