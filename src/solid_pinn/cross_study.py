"""Independent NMC622 OCV reference and predeclared cross-study sensitivity.

IMOTHEP Consortium (KIT/AIT), D4.9 Final Battery Model Documentation
(20 June 2023), Table 3, p.12.
https://www.imothep-project.eu/files/d4-9-final-battery-model-documentation.pdf

Different cell chemistry, electrolyte, temperature and stoichiometric window!
No author experimental data from IMOTHEP are redistributed.
"""
from collections.abc import Callable
import numpy as np


def imothep_nmc622_ocv(soc: np.ndarray | float, stage: str) -> np.ndarray:
    """AIT-fitted single-valued NMC622 OCV in volts.

    IMOTHEP uses x=c_s/c_s,max. SOLiD-PINN uses soc=1-x.
    Does not reproduce charge/discharge hysteresis of Dessantis (2024).
    The usable stoichiometric window is NOT established.
    """
    if stage not in {"charge", "discharge"}:
        raise ValueError("stage must be charge or discharge")
    s = np.asarray(soc, dtype=float)
    if not np.isfinite(s).all():
        raise ValueError("SoC must be finite")
    # Match existing paper-OCV lookup clipping convention. Extrapolation risk
    # must still be audited: clipped surface states are NOT validated physics.
    x = 1.0 - np.clip(s, 0.0, 1.0)
    return (
        7.066 * np.exp(-((x + 1.479) / 1.871) ** 2)
        + 1.725 * np.exp(-((x - 0.877) / 0.6847) ** 2)
        + 0.1751 * np.exp(-((x - 0.9245) / 0.1443) ** 2)
    )


def blended_ocv(paper_ocv: Callable, external_fraction: float) -> Callable:
    """Sensitivity probe, NOT a physics-based mixture or trained parameter.

    Only predeclare weights before seeing held-out C-rates.
    """
    if not np.isfinite(external_fraction) or not 0 <= external_fraction <= 1:
        raise ValueError("external_fraction must be between zero and one")

    def result(soc: np.ndarray | float, stage: str) -> np.ndarray:
        return ((1.0 - external_fraction) * paper_ocv(soc, stage)
                + external_fraction * imothep_nmc622_ocv(soc, stage))
    return result
