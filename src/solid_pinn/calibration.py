"""Calibration to external charge/discharge CSV traces with held-out rate evaluation.

This is explicitly a preliminary model-fitting workflow. The voltage trace and
OCV curve must be supplied; the repository ships neither source-paper traces
nor digitised derivative data. Fitting is limited to C/20 by design. All
results remain conditional on the reduced P2D model and data provenance.
"""

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from .numerical import ReducedP2D
from .parameters import Parameters


_REQUIRED = {"time_h", "voltage_v", "stage"}


def load_trace_csv(path: str | Path) -> pd.DataFrame:
    """Load a single C-rate's absolute-time, stage-tagged measured curve.

    Validates the source schema but deliberately does not guess units or shift
    measurement times. Users must document the clock's provenance externally.
    """
    df = pd.read_csv(path)
    if not _REQUIRED.issubset(df.columns):
        raise ValueError(f"Missing required columns: {sorted(_REQUIRED - set(df.columns))}")
    df = df.loc[:, ["time_h", "voltage_v", "stage"]].copy()
    if set(df.stage.unique()) != {"charge", "discharge"}:
        raise ValueError("Trace must contain both charge and discharge stages")
    for col in ["time_h", "voltage_v"]:
        df[col] = pd.to_numeric(df[col], errors="raise")
        if not np.isfinite(df[col]).all():
            raise ValueError(f"{col} contains invalid numeric values")
    if (df.time_h < 0).any():
        raise ValueError("Time must be nonnegative")
    for name, group in df.groupby("stage"):
        if len(group) < 3:
            raise ValueError(f"Stage {name} needs at least 3 observations")
        if not np.all(np.diff(group.time_h) > 0):
            raise ValueError(f"Stage {name} time_h must be strictly increasing")
    return df


def trace_diagnostics(sim: pd.DataFrame, measured: pd.DataFrame) -> dict:
    """Stage-relative voltage RMSE and duration mismatch, with no extrapolation.

    Endpoint differences are reported separately. Only overlapping time points
    contribute to voltage RMSE, and `coverage_fraction` exposes missing times.
    """
    diagnostics = {}
    for stage in ("charge", "discharge"):
        pred = sim.loc[sim.stage == stage]
        obs = measured.loc[measured.stage == stage]
        if len(pred) < 2 or len(obs) < 2:
            raise ValueError(f"Insufficient points in stage: {stage}")
        t_pred = pred.time_h.to_numpy() - float(pred.time_h.iloc[0])
        t_obs = obs.time_h.to_numpy() - float(obs.time_h.iloc[0])
        obs_v = obs.voltage_v.to_numpy(float)
        inside = t_obs <= t_pred[-1]
        if not inside.any():
            raise ValueError(f"No overlapping time support in {stage}")
        pred_v = np.interp(t_obs[inside], t_pred, pred.voltage_v)
        diff = pred_v - obs_v[inside]
        diagnostics[stage] = {
            "rmse_v": float(np.sqrt(np.mean(diff**2))),
            "mae_v": float(np.mean(np.abs(diff))),
            "coverage_fraction": float(np.mean(inside)),
            "duration_error_h": float(t_pred[-1] - t_obs[-1]),
            "simulated_duration_h": float(t_pred[-1]),
            "observed_duration_h": float(t_obs[-1]),
            "n_observations": int(len(t_obs)),
        }
    return diagnostics


def _voltage_residuals(sim: pd.DataFrame, measured: pd.DataFrame, per_stage_points=64,
                       endpoint_penalty_v_per_h=0.05) -> np.ndarray:
    """Fit aligned stage voltage plus a duration penalty in the same voltage units.

    Nonoverlap is not silently dropped: we hold the terminal voltage beyond
    simulated support and add an explicitly scaled duration penalty. This avoids
    rewarding parameters simply because the simulated curve terminates early.
    """
    chunks = []
    for stage in ("charge", "discharge"):
        pred = sim.loc[sim.stage == stage]
        obs = measured.loc[measured.stage == stage]
        t_sim = pred.time_h.to_numpy() - float(pred.time_h.iloc[0])
        t_obs = obs.time_h.to_numpy() - float(obs.time_h.iloc[0])
        v_obs = obs.voltage_v.to_numpy(float)
        samples = np.linspace(0, 1, per_stage_points)
        t_target = np.interp(samples, np.linspace(0,1,len(t_obs)),t_obs)
        v_target = np.interp(t_target,t_obs,v_obs)
        v_pred = np.interp(t_target,t_sim,pred.voltage_v.to_numpy(float))
        chunks.append((v_pred-v_target)/np.sqrt(2*per_stage_points))
        duration_delta = t_sim[-1] - t_obs[-1]
        chunks.append(np.array([endpoint_penalty_v_per_h*duration_delta]))
    return np.concatenate(chunks)


@dataclass(frozen=True)
class CalibrationResult:
    calibrated_parameters: Parameters
    fit_report: dict
    simulation: pd.DataFrame


def calibrate_c20(
    measured_c20: pd.DataFrame,
    ocv_function: Callable,
    base: Parameters | None = None,
    nx: int = 4,
    nr: int = 6,
    dt_s: float = 300,
    max_nfev: int = 25,
    fit_initial_soc: bool = True,
) -> CalibrationResult:
    """Fit cathode exchange current and optionally initial SoC ONLY at C/20.

    Inverting just two heuristic quantities avoids false confidence about the
    many electrochemical degrees of freedom not identified by one C-rate.
    """
    if not {"charge","discharge"}.issubset(set(measured_c20.stage.unique())):
        raise ValueError("C/20 training trace requires both charge and discharge")
    p0 = base or Parameters()
    x0 = [np.log10(p0.exchange_current_cathode_a_m2)]
    lo, hi = [np.log10(1e-4)], [np.log10(10.0)]
    if fit_initial_soc:
        x0.append(p0.initial_soc)
        lo.append(0.001)
        hi.append(0.20)
    attempts = 0
    best = None

    def decode(x):
        return replace(p0, exchange_current_cathode_a_m2=float(10**x[0]),
                       initial_soc=float(x[1]) if fit_initial_soc else p0.initial_soc)

    def residual(x):
        nonlocal attempts,best
        attempts += 1
        params = decode(x)
        try:
            sim = ReducedP2D(params=params, nx=nx, nr=nr,
                            ocv_function=ocv_function).simulate_cycle(20,dt_s)
            residual_vec = _voltage_residuals(sim, measured_c20)
        except (RuntimeError, ValueError, OverflowError, FloatingPointError):
            return np.full(130,1e3)
        score=float(np.sum(residual_vec**2))
        if best is None or score < best[0]:
            best=(score,x.copy())
        return residual_vec

    opt=least_squares(residual,x0,bounds=(lo,hi),max_nfev=max_nfev,
                      diff_step=0.002,xtol=1e-3,ftol=1e-3,gtol=1e-3)
    if best is None:
        raise RuntimeError("All calibration simulations failed")
    # If the optimizer failed during a final trial, use best evaluated point.
    p_fit=decode(best[1]);sim=ReducedP2D(p_fit,nx=nx,nr=nr,
                     ocv_function=ocv_function).simulate_cycle(20,dt_s)
    report={"training_rate":"C/20","param_provenance":"estimated from supplied C/20 trace only",
            "fitted_parameters":{
                "exchange_current_cathode_a_m2":p_fit.exchange_current_cathode_a_m2,
                "initial_soc":p_fit.initial_soc if fit_initial_soc else "fixed"},
            "fixed_paper_parameters":{"kappa_sse_s_m":p_fit.kappa_sse_s_m,
                                       "particle_diffusivity_m2_s":p_fit.particle_diffusivity_m2_s},
            "objective_sum_squared":float(best[0]),"optimiser_success":bool(opt.success),
            "optimiser_message":str(opt.message),"objective_evaluations":attempts,
            "diagnostics_c20":trace_diagnostics(sim,measured_c20),
            "warnings":["Derived figure traces are approximate and not experimental raw data",
                        "C/20 observations alone do not identify all model transport and kinetic parameters",
                        "Parameter uncertainties and convergence are NOT established"]}
    return CalibrationResult(p_fit,report,sim)


def validate_heldout(result: CalibrationResult, ocv_function: Callable,
                     heldout: dict[int,pd.DataFrame],nx=4,nr=6,dt_s=300):
    """Predict C/10 and C/5 without refitting; refuses training-rate leakage."""
    if set(heldout) - {10,5}:
        raise ValueError("Only truly held-out rates C/10 and C/5 are accepted")
    output={}
    for rate,exp in heldout.items():
        sim=ReducedP2D(result.calibrated_parameters,nx=nx,nr=nr,
                        ocv_function=ocv_function).simulate_cycle(rate,dt_s)
        output[rate]={"diagnostics":trace_diagnostics(sim,exp),"simulation":sim}
    return output
