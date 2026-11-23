"""Auditable C/20-only calibration; no copyrighted digitised data are bundled.

Example:
python scripts/calibrate_c20.py \
 --charge-ocv /path/charge.csv --discharge-ocv /path/discharge.csv \
 --c20 /path/c20.csv --c10 /path/c10.csv --c5 /path/c5.csv
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from solid_pinn.calibration import (
    calibrate_c20, load_trace_csv, trace_diagnostics, validate_heldout,
)
from solid_pinn.numerical import ReducedP2D
from solid_pinn.ocv import experimental_ocv_from_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Preliminary C/20-only P2D calibration")
    for name in ("charge-ocv", "discharge-ocv", "c20"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in ("c10", "c5"):
        parser.add_argument(f"--{name}", type=Path)
    parser.add_argument("--outdir", type=Path, default=Path("outputs/calibration"))
    parser.add_argument("--max-nfev", type=int, default=25)
    parser.add_argument("--dt", type=float, default=300.0)
    parser.add_argument("--nx", type=int, default=4)
    parser.add_argument("--nr", type=int, default=6)
    parser.add_argument("--fit-j0-only", action="store_true")
    args=parser.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    ocv=experimental_ocv_from_csv(str(args.charge_ocv),str(args.discharge_ocv))
    measured=load_trace_csv(args.c20)
    baseline=ReducedP2D(nx=args.nx,nr=args.nr,ocv_function=ocv).simulate_cycle(20,args.dt)
    result=calibrate_c20(measured,ocv,nx=args.nx,nr=args.nr,dt_s=args.dt,
                         max_nfev=args.max_nfev,fit_initial_soc=not args.fit_j0_only)
    heldout={}
    if args.c10: heldout[10]=load_trace_csv(args.c10)
    if args.c5: heldout[5]=load_trace_csv(args.c5)
    checked=validate_heldout(result,ocv,heldout,nx=args.nx,nr=args.nr,dt_s=args.dt)
    diagnostics={"calibration":result.fit_report,
                 "baseline_c20":trace_diagnostics(baseline,measured),
                 "heldout":{f"C/{r}":v["diagnostics"] for r,v in checked.items()},
                 "input_provenance":{
                     "charge_ocv":str(args.charge_ocv),"discharge_ocv":str(args.discharge_ocv),
                     "c20":str(args.c20),"c10":str(args.c10) if args.c10 else None,
                     "c5":str(args.c5) if args.c5 else None,
                     "interpretation":"PRELIMINARY. No claim of full P2D reproduction or raw measurement"},
                 "numerical_configuration":{"nx":args.nx,"nr":args.nr,"dt_s":args.dt}}
    (args.outdir/"calibration_report.json").write_text(json.dumps(diagnostics,indent=2))
    baseline.to_csv(args.outdir/"baseline_C20.csv",index=False)
    result.simulation.to_csv(args.outdir/"fit_C20.csv",index=False)
    for rate,record in checked.items():
        record["simulation"].to_csv(args.outdir/f"prediction_C{rate}.csv",index=False)
    fig,axes=plt.subplots(1,3,figsize=(14,4.2))
    for ax,(rate,observed,predicted) in zip(axes,[(20,measured,result.simulation)] +
                            [(rate,heldout[rate],checked[rate]["simulation"]) for rate in sorted(heldout)]):
        for stage in ("charge","discharge"):
            o=observed[observed.stage==stage]; p=predicted[predicted.stage==stage]
            ax.plot(o.time_h,o.voltage_v,".",ms=2,alpha=.7,label=f"provided trace {stage}")
            ax.plot(p.time_h,p.voltage_v,"-",lw=1.3,label=f"model {stage}")
        ax.set(xlabel="Time (h)",ylabel="Cell voltage (V)",title=f"C/{rate}"+(" fit" if rate==20 else " held out"))
        ax.grid(alpha=.25)
    for a in axes: a.legend(fontsize=6)
    fig.suptitle("Preliminary model vs supplied curves — not author raw data")
    fig.tight_layout()
    fig.savefig(args.outdir/"diagnostics.png",dpi=180)
    plt.close(fig)
    print(json.dumps(diagnostics,indent=2))

if __name__=="__main__":
    main()
