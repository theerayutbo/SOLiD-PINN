"""Evaluate a local, authorized COMSOL C/20 sequential-cycle voltage reference."""
import argparse
import json
from dataclasses import replace
from pathlib import Path
import pandas as pd
from solid_pinn.comsol_c20 import load_c20_cycle, compare_cycle
from solid_pinn.parameters import Parameters
from solid_pinn.numerical import ReducedP2D
from solid_pinn.ocv import ocv_v, experimental_ocv_from_csv


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source")
    p.add_argument("--charge-ocv"); p.add_argument("--discharge-ocv")
    p.add_argument("--outdir",default="outputs/comsol_c20")
    p.add_argument("--nx",type=int,default=6);p.add_argument("--nr",type=int,default=10)
    p.add_argument("--dt",type=float,default=60.)
    a=p.parse_args()
    if bool(a.charge_ocv)!=bool(a.discharge_ocv): p.error("provide both OCV files")
    reference,meta=load_c20_cycle(a.source)
    cases=[("synthetic_frozen",.0770454572,.0566011934,ocv_v)]
    if a.charge_ocv:
        u=experimental_ocv_from_csv(a.charge_ocv,a.discharge_ocv)
        cases.extend([("digitized_frozen",.0770454572,.0566011934,u),
            ("digitized_fully_lithiated",0.,.0566011934,u)])
        cases.extend((f"digitized_soc0_j{j}",0.,j,u) for j in (.12,.25,.5,1.))
    dest=Path(a.outdir);dest.mkdir(parents=True,exist_ok=True)
    rows=[];failures=[]
    for name,s0,j0,u in cases:
        par=replace(Parameters(),sigma_cathode_s_m=.17,initial_soc=s0,
                    exchange_current_cathode_a_m2=j0)
        solver=ReducedP2D(par,a.nx,a.nr,ocv_function=u)
        states={};c=None
        try:
            for stage in ("charge","discharge"):
                states[stage],c=solver.simulate_stage(stage,c,20,dt_s=a.dt)
        except RuntimeError as exc:
            failures.append({"case":name,"error":str(exc)});continue
        rows.extend(dict(case=name,**r) for r in compare_cycle(reference,states))
        pd.concat(states.values(),ignore_index=True).to_csv(dest/f"{name}.csv",index=False)
    pd.DataFrame(rows).to_csv(dest/"comparison.csv",index=False)
    meta.update(nx=a.nx,nr=a.nr,dt_s=a.dt,sigma_cathode_s_m=.17,failures=failures,
        warning="Voltage-only reference; parameter equivalence, current and cutoff not confirmed.")
    (dest/"metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf8")
    print(pd.DataFrame(rows).to_string(index=False))
    print(json.dumps(failures,indent=2))


if __name__=="__main__":
    main()
