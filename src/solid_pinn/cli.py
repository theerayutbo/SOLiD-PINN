"""Command line entrypoint."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .numerical import ReducedP2D
from .ocv import experimental_ocv_from_csv
from .validation import capacity_ah


def simulate(rates: list[int], outdir: Path, dt_s: float, nx: int, nr: int,
             charge_ocv_csv: Path | None = None, discharge_ocv_csv: Path | None = None) -> None:
    outdir.mkdir(parents=True,exist_ok=True)
    if (charge_ocv_csv is None) != (discharge_ocv_csv is None):
        raise ValueError("Supply BOTH measured --charge-ocv and --discharge-ocv files")
    observed_ocv = (experimental_ocv_from_csv(str(charge_ocv_csv), str(discharge_ocv_csv))
                    if charge_ocv_csv else None)
    model = ReducedP2D(nx=nx,nr=nr, **({"ocv_function": observed_ocv} if observed_ocv else {}))
    fig, ax = plt.subplots(figsize=(8,5))
    summary=[]
    for r in rates:
        df = model.simulate_cycle(c_rate_denominator=r,dt_s=dt_s)
        df.to_csv(outdir/f"synthetic_C_{r}.csv",index=False)
        for stage in ("charge","discharge"):
            seg=df.loc[df.stage==stage]
            ax.plot(seg.time_h,seg.voltage_v,label=f"C/{r} {stage}")
            summary.append({"rate":f"C/{r}","stage":stage,
                            "capacity_mah":capacity_ah(df,stage)*1000,
                            "elapsed_h":seg.time_h.iloc[-1]-seg.time_h.iloc[0]})
    pd.DataFrame(summary).to_csv(outdir/"summary.csv",index=False)
    ax.set(xlabel="Time (h)",ylabel="Cell voltage (V)",
           title=("SOLiD-PINN reduced P2D (measured OCV, kinetics still assumed)"
                  if observed_ocv else "SOLiD-PINN numerical prototype (illustrative OCV, NOT Fig. 5 reproduction)"))
    ax.legend(fontsize=8,ncol=2)
    fig.tight_layout()
    fig.savefig(outdir/"synthetic_voltage_curves.png",dpi=170)
    plt.close(fig)
    print(f"Wrote numerical prototype results to {outdir}")


def main() -> None:
    parser=argparse.ArgumentParser(prog="solid-pinn",description="Experimental solid-state battery modelling research scaffold")
    sub=parser.add_subparsers(dest="command",required=True)
    s=sub.add_parser("simulate",help="Simulate reduced P2D charge/discharge curves")
    s.add_argument("--rates",nargs="+",type=int,default=[20,10,5])
    s.add_argument("--outdir",type=Path,default=Path("outputs"))
    s.add_argument("--dt",type=float,default=300.0)
    s.add_argument("--nx",type=int,default=6)
    s.add_argument("--nr",type=int,default=10)
    s.add_argument("--charge-ocv",type=Path)
    s.add_argument("--discharge-ocv",type=Path)
    n=sub.add_parser("pinn-demo",help="Synthetic PINN inverse problem for Li6PS5Cl conductivity")
    n.add_argument("--epochs",type=int,default=900)
    a=parser.parse_args()
    if a.command=="simulate":
        simulate(a.rates,a.outdir,a.dt,a.nx,a.nr,a.charge_ocv,a.discharge_ocv)
    else:
        from .pinn import invert_sse_conductivity_synthetic
        result=invert_sse_conductivity_synthetic(epochs=a.epochs)
        print(f"True kappa: {result.true_conductivity_s_m:.6f} S/m")
        print(f"PINN inferred kappa: {result.estimated_conductivity_s_m:.6f} S/m")
        print(f"Relative error: {100*result.relative_error:.2f}%")
        print("Synthetic inverse problem only; not a paper Fig. 5 reproduction")


if __name__=="__main__":
    main()
