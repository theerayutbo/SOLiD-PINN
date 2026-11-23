"""ILLUSTRATIVE pseudo-OCV curves, NOT measurements and NOT digitised paper curves.

Paper Fig. 4 contains charge and discharge pseudo-OCV curves with ~33 mV
polarisation at cell SoC 50%. The *actual* arrays should be supplied by
an author / calibrated digitisation before claiming a paper reproduction.
"""

import numpy as np
from scipy.interpolate import PchipInterpolator

# Illustrative knot points ONLY. These are intentionally not cited as paper data.
_SOC_KNOTS = np.array([0.00, 0.03, 0.1, 0.3, 0.5, 0.7, 0.9, 0.98, 1.0])
_MID_V = np.array([2.78, 3.58, 3.65, 3.71, 3.75, 3.82, 3.99, 4.13, 4.20])
_BASE = PchipInterpolator(_SOC_KNOTS, _MID_V, extrapolate=False)


def ocv_v(soc: np.ndarray | float, stage: str) -> np.ndarray:
    """Return illustrative U(SOC). SoC is cell SoC = 1-c_s/c_s,max."""
    if stage not in {"charge", "discharge"}:
        raise ValueError("stage must be 'charge' or 'discharge'")
    offset = 0.0165 if stage == "charge" else -0.0165
    return np.asarray(_BASE(np.clip(soc, 0, 1)) + offset)


def experimental_ocv_from_csv(charge_path: str, discharge_path: str):
    """Load independently measured OCV curves (SOC, voltage_v) for both stages.

    Returns a callable compatible with ReducedP2D(ocv_function=...).
    CSV points must cover [0,1] so no out-of-bounds extrapolation is needed.
    """
    import pandas as pd

    curves = {}
    for stage, path in (("charge", charge_path), ("discharge", discharge_path)):
        df = pd.read_csv(path)
        if not {"soc", "voltage_v"}.issubset(df.columns):
            raise ValueError(f"{stage} OCV CSV needs 'soc' and 'voltage_v' columns")
        df = df.sort_values("soc")
        xs, ys = df.soc.to_numpy(float), df.voltage_v.to_numpy(float)
        if len(xs) < 3 or not (np.isfinite(xs).all() and np.isfinite(ys).all()):
            raise ValueError(f"{stage} OCV needs >= 3 finite points")
        if np.any(np.diff(xs) <= 0) or xs[0] > 0 or xs[-1] < 1:
            raise ValueError(f"{stage} OCV SOC points must be unique and cover 0..1")
        curves[stage] = PchipInterpolator(xs,ys,extrapolate=False)

    def observed_ocv(soc: np.ndarray | float, stage: str) -> np.ndarray:
        if stage not in curves:
            raise ValueError("stage must be charge or discharge")
        return np.asarray(curves[stage](np.clip(soc,0,1)))

    return observed_ocv
