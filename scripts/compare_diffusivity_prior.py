"""Cross-study NMC622 D_s sensitivity, not direct material calibration.

IMOTHEP KIT/AIT D4.9 (2023), Table 2 (PDF p.11):
D_s=4.84e-14 m2/s; Dessantis (2024) Table 2: D_s=2e-13 m2/s.
Fit exchange-current density and initial SoC ONLY at C/20.
"""
import argparse
import json
from dataclasses import replace
from pathlib import Path

from solid_pinn.parameters import Parameters
from solid_pinn.ocv import experimental_ocv_from_csv
from solid_pinn.calibration import calibrate_c20, load_trace_csv, validate_heldout

IMOTHEP_DIFFUSIVITY_M2_S = 4.84e-14


def run(c20,c10,c5,charge_ocv,discharge_ocv,outdir,max_nfev=25):
    ocv=experimental_ocv_from_csv(charge_ocv,discharge_ocv)
    p=replace(Parameters(),particle_diffusivity_m2_s=IMOTHEP_DIFFUSIVITY_M2_S)
    fit=calibrate_c20(load_trace_csv(c20),ocv,base=p,max_nfev=max_nfev)
    heldout=validate_heldout(fit,ocv,{10:load_trace_csv(c10),5:load_trace_csv(c5)})
    result={"status":"figure digitisation only; not author raw data",
            "external_diffusivity_m2_s":IMOTHEP_DIFFUSIVITY_M2_S,
            "source":"IMOTHEP D4.9 Table 2, different cell/temperature",
            "training":fit.fit_report,
            "heldout":{f"C/{rate}":x["diagnostics"] for rate,x in heldout.items()}}
    output=Path(outdir);output.mkdir(parents=True,exist_ok=True)
    (output/"diffusivity_sensitivity.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("c20","c10","c5","charge-ocv","discharge-ocv"):
        p.add_argument("--"+arg,required=True)
    p.add_argument("--outdir",default="outputs/diffusivity_sensitivity")
    args=p.parse_args()
    print(json.dumps(run(args.c20,args.c10,args.c5,args.charge_ocv,
                         args.discharge_ocv,args.outdir),indent=2))


if __name__=="__main__":
    main()
