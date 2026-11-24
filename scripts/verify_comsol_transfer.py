"""Run an authorized local COMSOL transfer and retain negative ablations."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from solid_pinn.comsol_transfer import read_model, TransferFEM
from solid_pinn.comsol_c20 import load_c20_cycle, compare_cycle

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model")
    p.add_argument("trace")
    p.add_argument("--outdir",default="outputs/comsol_transfer")
    p.add_argument("--nx",type=int,default=4)
    p.add_argument("--nr",type=int,default=10)
    a=p.parse_args()
    m=read_model(a.model)
    reference,meta=load_c20_cycle(a.trace)
    dest=Path(a.outdir);dest.mkdir(parents=True,exist_ok=True)
    rows=[];failures=[]
    for name,R,D in (("transfer_full",True,True),("no_R",False,True),("constant_D",True,False)):
        solver=TransferFEM(m,a.nx,a.nr,use_R=R,use_D=D)
        c=None;states={}
        try:
            for stage in ("charge","discharge"):
                states[stage],c=solver.stage(stage,20,c)
            rows.extend(dict(case=name,**row) for row in compare_cycle(reference,states))
            pd.concat(states.values(),ignore_index=True).to_csv(dest/(name+".csv"),index=False)
        except RuntimeError as exc:
            failures.append(dict(case=name,error=str(exc)))
    result=pd.DataFrame(rows)
    result.to_csv(dest/"metrics.csv",index=False)
    print(result.to_string(index=False))
    if failures: raise RuntimeError(str(failures))

if __name__=="__main__":
    main()
