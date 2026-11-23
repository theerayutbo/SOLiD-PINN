"""C/20-only cross-study NMC622 OCV sensitivity, C/10 & C/5 held out.

Requires private CSVs extracted from legally accessed source data.
Does not redistribute copyrighted source-figure derivatives.
"""
import argparse
import json
from pathlib import Path
import pandas as pd
from solid_pinn.calibration import calibrate_c20, load_trace_csv, validate_heldout
from solid_pinn.cross_study import blended_ocv
from solid_pinn.ocv import experimental_ocv_from_csv

# NEVER select the winning weight using held-out performance.
EXPERIMENTS = (("dessantis_only", 0.0),
               ("imothep_25pct", 0.25),
               ("imothep_50pct", 0.50))


def run_comparison(c20, c10, c5, charge_ocv, discharge_ocv, outdir,
                   max_nfev=25, dt=300, nx=4, nr=6):
    destination = Path(outdir)
    destination.mkdir(parents=True, exist_ok=True)
    train = load_trace_csv(c20)
    heldout = {10: load_trace_csv(c10), 5: load_trace_csv(c5)}
    source_ocv = experimental_ocv_from_csv(charge_ocv, discharge_ocv)
    rows, reports = [], {}
    for name, fraction in EXPERIMENTS:
        ocv = blended_ocv(source_ocv, fraction)
        calibrated = calibrate_c20(train, ocv, nx=nx, nr=nr,
                                   dt_s=dt, max_nfev=max_nfev)
        validated = validate_heldout(calibrated, ocv, heldout,
                                    nx=nx, nr=nr, dt_s=dt)
        all_metrics = {20: calibrated.fit_report["diagnostics_c20"]}
        all_metrics.update({rate: record["diagnostics"]
                            for rate, record in validated.items()})
        for rate, stages in all_metrics.items():
            for stage, metrics in stages.items():
                rows.append({"model": name, "external_fraction": fraction,
                             "rate": rate, "stage": stage,
                             "split": "train" if rate == 20 else "held_out",
                             "rmse_mv": metrics["rmse_v"] * 1000,
                             "mae_mv": metrics["mae_v"] * 1000,
                             "coverage": metrics["coverage_fraction"],
                             "duration_error_h": metrics["duration_error_h"]})
        reports[name] = {
            "external_fraction": fraction, "training_rate": "C/20",
            "external_source": "IMOTHEP D4.9 Table 3 (different cell, 60 C)",
            "fit_parameters": calibrated.fit_report["fitted_parameters"],
            "optimizer_success": calibrated.fit_report["optimiser_success"],
            "heldout_rates": ["C/10", "C/5"],
        }
        calibrated.simulation.to_csv(destination / f"{name}_C20.csv", index=False)
        for rate, record in validated.items():
            record["simulation"].to_csv(
                destination / f"{name}_C{rate}.csv", index=False)
    metrics_df = pd.DataFrame(rows)
    metrics_df.to_csv(destination / "cross_study_metrics.csv", index=False)
    (destination / "cross_study_report.json").write_text(
        json.dumps({
            "status": "exploratory, digitized curves, NOT author raw data",
            "sources": [
                "https://doi.org/10.1016/j.ceja.2024.100610",
                "https://www.imothep-project.eu/files/d4-9-final-battery-model-documentation.pdf",
            ], "models": reports,
            "critical_caveats": [
                "Different electrolyte, temperature and stoichiometric window",
                "IMOTHEP curve has no independent charge/discharge hysteresis",
                "Blending different source OCV functions is only a sensitivity test",
                "Held-out C/10, C/5 must never drive weight tuning",
                "No separate full-P2D numerical validation or raw measurements",
            ], "mesh": {"nx": nx, "nr": nr, "dt_s": dt}
        }, indent=2), encoding="utf-8")
    return metrics_df


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("charge-ocv", "discharge-ocv", "c20", "c10", "c5"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--outdir", default="outputs/cross_study")
    parser.add_argument("--max-nfev", type=int, default=25)
    parser.add_argument("--nx", type=int, default=4)
    parser.add_argument("--nr", type=int, default=6)
    parser.add_argument("--dt", type=float, default=300.)
    x = parser.parse_args()
    r = run_comparison(x.c20,x.c10,x.c5,x.charge_ocv,x.discharge_ocv,
                       x.outdir,x.max_nfev,x.dt,x.nx,x.nr)
    print(r.to_string(index=False))


if __name__ == "__main__":
    main()
