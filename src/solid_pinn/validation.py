"""Metrics and protocol for eventual Fig. 5/Table 3 experimental comparison."""

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid

PAPER_TABLE3_PERCENT = {
    20: {"charge": 0.6, "discharge": -2.5},
    10: {"charge": -2.4, "discharge": -3.1},
    5: {"charge": -0.5, "discharge": -2.6},
}


def capacity_ah(frame: pd.DataFrame, stage: str) -> float:
    """Integral |I|dt along one stage (voltage cutoffs determine duration)."""
    x = frame.loc[frame["stage"] == stage]
    if len(x) < 2:
        return 0.0
    return float(trapezoid(np.abs(x["current_a"]), x["time_h"]))


def capacity_error_percent(pred_ah: float, experimental_ah: float) -> float:
    if experimental_ah <= 0:
        raise ValueError("Experimental capacity must be positive")
    return 100.0*(pred_ah-experimental_ah)/experimental_ah


def compare_voltage_curve(sim: pd.DataFrame, exp: pd.DataFrame) -> pd.DataFrame:
    """Compare two records of the same stage using common time support.

    Expects exp columns [time_h, voltage_v, stage]. Does not extrapolate.
    Original author data are not shipped with this repository.
    """
    out = []
    for stage in ("charge", "discharge"):
        a = sim.loc[sim.stage == stage].sort_values("time_h")
        b = exp.loc[exp.stage == stage].sort_values("time_h")
        if len(a)<2 or len(b)<2:
            continue
        t = b.time_h.to_numpy(dtype=float)
        valid = (t>=a.time_h.iloc[0]) & (t<=a.time_h.iloc[-1])
        if not np.any(valid):
            continue
        y_pred = np.interp(t[valid],a.time_h,a.voltage_v)
        y_true = b.voltage_v.to_numpy()[valid]
        out.append({"stage":stage,"n":int(np.sum(valid)),
                    "rmse_v":float(np.sqrt(np.mean((y_pred-y_true)**2))),
                    "mae_v":float(np.mean(np.abs(y_pred-y_true)))})
    return pd.DataFrame(out)
