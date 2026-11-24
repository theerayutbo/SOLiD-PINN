"""Compare authorized COMSOL result CSVs against FVM with matched protocol.
CSV: time_s,voltage_v,soc,stage,rate,sigma_cathode_s_m. Each stage starts at its local t=0.
The user must first verify geometry, signs, parameters, initial conditions,
OCV provenance, events and units using the COMSOL equation audit.
"""
import argparse
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
from solid_pinn.parameters import Parameters
from solid_pinn.numerical import ReducedP2D


def compare(path, nx=12, nr=20, dt=30.):
    data=pd.read_csv(path)
    required={"time_s","voltage_v","soc","stage","rate","sigma_cathode_s_m"}
    if not required<=set(data): raise ValueError("missing required columns")
    if data.empty: raise ValueError("empty COMSOL data")
    if not np.allclose(data.sigma_cathode_s_m.to_numpy(float), Parameters().sigma_cathode_s_m, rtol=0, atol=1e-12):
        raise ValueError("COMSOL conductivity does not match corrected v0.6.1 benchmark (0.17 S/m)")
    if set(zip(data.rate,data.stage)) != {(r,s) for r in (20,10,5) for s in ("charge","discharge")}:
        raise ValueError("all six matched stages are required")
    rows=[]
    for (rate,stage),d in data.groupby(["rate","stage"]):
        if rate not in (20,10,5) or stage not in ("charge","discharge"): raise ValueError("invalid protocol")
        d=d.sort_values("time_s")
        t=d.time_s.to_numpy(float);v=d.voltage_v.to_numpy(float);s=d.soc.to_numpy(float)
        if len(t)<2 or not np.isfinite(np.column_stack([t,v,s])).all() or abs(t[0])>1e-8 or np.any(np.diff(t)<=0):
            raise ValueError("invalid stage-local time or nonfinite results")
        s0=.0770454572 if stage=="charge" else .90
        if abs(s[0]-s0)>1e-5: raise ValueError("initial SOC mismatch")
        if np.any((s<0)|(s>1)): raise ValueError("SOC must be a fraction in [0,1]")
        margin=np.minimum(4.2-v,.995-s) if stage=="charge" else np.minimum(v-2.7,s-.005)
        if abs(margin[-1])>1e-4 or np.any(margin[:-1]<-1e-4):
            raise ValueError("COMSOL stage must end at first matched voltage/SOC cutoff")
        p=replace(Parameters(),initial_soc=s0,exchange_current_cathode_a_m2=.0566011934)
        f,_=ReducedP2D(p,nx,nr).simulate_stage(stage,c_rate_denominator=int(rate),dt_s=dt)
        tf=f.time_h.to_numpy()*3600
        end=min(t[-1],tf[-1]);tt=np.linspace(0,end,2001)
        if end<=0: raise ValueError("no common time interval")
        I=p.current_a(rate)*(-1 if stage=="charge" else 1)
        rows.append(dict(benchmark_id="v061_sigma017",sigma_cathode_s_m=p.sigma_cathode_s_m,rate=rate,stage=stage,initial_soc=s0,voltage_rmse_mv=1000*np.sqrt(np.mean((np.interp(tt,t,v)-np.interp(tt,tf,f.voltage_v))**2)),capacity_difference_pct=100*(tf[-1]-t[-1])/t[-1],mass_comsol_pct_nominal=100*np.max(abs(s-(s0-I*t/(3600*p.nominal_capacity_ah)))),common_duration_fraction=end/max(t[-1],tf[-1]),status="conditional_on_verified_model_and_cutoff"))
    return pd.DataFrame(rows)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv");p.add_argument("--out",default="outputs/comsol_comparison.csv")
    args=p.parse_args(); r=compare(args.csv);dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True);r.to_csv(dest,index=False);print(r.to_string(index=False))
