#!/usr/bin/env python3
"""v0.5 predeclared Li|LPSCl ASR scenarios; local private data ONLY.

Never select interface resistance using C/10 or C/5. The 0.8 Ohm cm2
microelectrode scale from Singh et al. 2023 is not a Dessantis-cell prior.
"""
import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from solid_pinn.calibration import load_trace_csv, trace_diagnostics, _voltage_residuals
from solid_pinn.ocv import experimental_ocv_from_csv
from solid_pinn.parameters import Parameters
from solid_pinn.transfer import (
    SeriesInterfaceReducedP2D, temperature_scenario, conductivity_activation_j_mol
)

ASR_GRID_OHM_CM2 = (0.0, 0.8, 5.0, 50.0, 200.0, 500.0)


def run_experiment(charge_ocv, discharge_ocv, c20, c10, c5, outdir,
                   j0=0.05660119341573162, initial_soc=0.07704545718494019,
                   nx=4, nr=6, dt_s=300.0):
    """Fixed v0.3 j0/SoC; select ASR on C/20 and only then assess held-outs."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    p = replace(Parameters(), exchange_current_cathode_a_m2=j0,
                initial_soc=initial_soc)
    ocv = experimental_ocv_from_csv(str(charge_ocv), str(discharge_ocv))
    obs = {20: load_trace_csv(c20), 10: load_trace_csv(c10),
           5: load_trace_csv(c5)}
    training = []
    for asr_cm2 in ASR_GRID_OHM_CM2:
        model = SeriesInterfaceReducedP2D(
            p, nx=nx, nr=nr, ocv_function=ocv,
            interface_asr_ohm_m2=asr_cm2 * 1e-4,
        )
        sim = model.simulate_cycle(20, dt_s)
        err = _voltage_residuals(sim, obs[20])
        d = trace_diagnostics(sim, obs[20])
        training.append({
            "asr_ohm_cm2": asr_cm2,
            "c20_objective": float(np.dot(err, err)),
            "c20_charge_rmse_mv": 1000 * d["charge"]["rmse_v"],
            "c20_discharge_rmse_mv": 1000 * d["discharge"]["rmse_v"],
        })
    train = pd.DataFrame(training)
    train.to_csv(outdir / "c20_training_asr_grid.csv", index=False)
    selected = float(train.loc[train.c20_objective.idxmin(), "asr_ohm_cm2"])

    heldout = []
    for label, asr_cm2 in (("baseline", 0.0), ("selected_by_c20", selected)):
        model = SeriesInterfaceReducedP2D(
            p, nx=nx, nr=nr, ocv_function=ocv,
            interface_asr_ohm_m2=asr_cm2 * 1e-4,
        )
        for rate in (20, 10, 5):
            sim = model.simulate_cycle(rate, dt_s)
            sim.to_csv(outdir / f"{label}_C{rate}.csv", index=False)
            d = trace_diagnostics(sim, obs[rate])
            for stage in ("charge", "discharge"):
                heldout.append({
                    "model": label, "rate": rate, "stage": stage,
                    "asr_ohm_cm2": asr_cm2,
                    "rmse_mv": 1000 * d[stage]["rmse_v"],
                    "duration_error_h": d[stage]["duration_error_h"],
                    "coverage": d[stage]["coverage_fraction"],
                })
    scores = pd.DataFrame(heldout)
    scores.to_csv(outdir / "comparison.csv", index=False)

    temperature_rows = []
    for t in (298.15, 313.15, 323.15):
        scenario = temperature_scenario(p, t)
        temperature_rows.append({
            "temperature_k": t, "kappa_sse_s_m": scenario.kappa_sse_s_m,
            "ds_m2_s": scenario.particle_diffusivity_m2_s,
        })
    pd.DataFrame(temperature_rows).to_csv(outdir / "temperature_sensitivity.csv", index=False)

    def mean_heldout(label):
        subset = scores[(scores.model == label) & scores.rate.isin([10, 5])]
        return float(subset.rmse_mv.mean())

    result = {
        "selected_asr_ohm_cm2_from_c20_only": selected,
        "asr_grid_ohm_cm2": list(ASR_GRID_OHM_CM2),
        "fixed_j0_a_m2": j0, "fixed_initial_soc": initial_soc,
        "mean_heldout_rmse_mv": {
            "baseline": mean_heldout("baseline"),
            "selected_by_c20": mean_heldout("selected_by_c20"),
        },
        "conductivity_activation_energy_j_mol": conductivity_activation_j_mol(),
        "data": "LOCAL digitised Dessantis 2024 Figure 4/5, not author raw data",
        "limitations": [
            "ASR grid is hypothetical except 0.8 literature microelectrode context, not transferable",
            "No refit of j0/SoC when ASR changes; ASR not uniquely identified",
            "OCV and kinetics temperature dependence are not calibrated",
            "Not independently validated against a custom PyBaMM/FEM solver",
        ],
    }
    (outdir / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    ap = argparse.ArgumentParser()
    for flag in ("charge-ocv", "discharge-ocv", "c20", "c10", "c5"):
        ap.add_argument("--" + flag, required=True, type=Path)
    ap.add_argument("--outdir", type=Path, default=Path("outputs/interface_temperature"))
    ap.add_argument("--nx", type=int, default=4)
    ap.add_argument("--nr", type=int, default=6)
    ap.add_argument("--dt", type=float, default=300.0)
    a = ap.parse_args()
    result = run_experiment(
        a.charge_ocv, a.discharge_ocv, a.c20, a.c10, a.c5,
        a.outdir, nx=a.nx, nr=a.nr, dt_s=a.dt,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
