"""Frozen C20 parameter transfer to C10/C5; local authorized inputs only."""
import argparse
import json
from pathlib import Path
import pandas as pd
from solid_pinn.comsol_transfer import read_model, TransferFEM
from solid_pinn.comsol_multirate import load_wide_cycle
from solid_pinn.comsol_c20 import compare_cycle


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model")
    p.add_argument("c10")
    p.add_argument("c5")
    p.add_argument("--outdir",default="outputs/comsol_multirate")
    p.add_argument("--nx",type=int,default=4)
    p.add_argument("--nr",type=int,default=10)
    a=p.parse_args()
    dest=Path(a.outdir);dest.mkdir(parents=True,exist_ok=True)
    model=read_model(a.model)
    rows=[];metadata=[]
    for rate,path in [(10,a.c10),(5,a.c5)]:
        solver=TransferFEM(model,a.nx,a.nr)
        ref,meta=load_wide_cycle(path,rate,solver.p.current_a(rate))
        metadata.append(dict(rate=rate,**meta))
        states={};c=None
        for stage in ("charge","discharge"):
            states[stage],c=solver.stage(stage,rate,c)
        rows.extend(dict(scenario="frozen_C20",rate=rate,**r)
                    for r in compare_cycle(ref,states))
        pd.concat(states.values(),ignore_index=True).to_csv(dest/f"C{rate}_predictions.csv",index=False)
    pd.DataFrame(rows).to_csv(dest/"metrics.csv",index=False)
    (dest/"metadata.json").write_text(json.dumps(metadata,indent=2))
    print(pd.DataFrame(rows).to_string(index=False))

if __name__=="__main__":
    main()
