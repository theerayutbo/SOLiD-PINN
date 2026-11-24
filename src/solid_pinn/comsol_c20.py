"""Import a COMSOL global voltage/time export for a sequential C/20 cycle.

This is a voltage-only simulation reference, not a matched six-stage benchmark
or experimental data. Do not infer SOC or model parameters from the header.
"""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd


def load_c20_cycle(path, time_tol_h=1e-8):
    """Return stage-local curves and provenance; preserve both event-side values.

    Require one paired-time switching event at the voltage maximum. Reject
    ambiguous traces rather than silently splitting at an arbitrary maximum.
    """
    path = Path(path)
    raw = path.read_bytes()
    header = {}
    for line in raw.decode("utf-8-sig").splitlines():
        if line.startswith("%") and ":" in line:
            key, value = line[1:].split(":", 1)
            header[key.strip()] = value.strip()
    data = np.loadtxt(path, comments="%", ndmin=2)
    if data.shape[1] != 2 or len(data) < 6 or not np.isfinite(data).all():
        raise ValueError("expected two finite numeric columns")
    t, v = data.T
    if abs(t[0]) > time_tol_h or np.any(np.diff(t) < -time_tol_h):
        raise ValueError("expected nondecreasing cycle time starting at zero")
    events = np.flatnonzero(np.abs(np.diff(t)) <= time_tol_h)
    if len(events) != 1:
        raise ValueError("expected exactly one paired-time switching event")
    k = int(events[0])
    if k < 2 or k >= len(t)-3 or k != int(np.argmax(v)) or v[k] <= v[k+1]:
        raise ValueError("ambiguous charge/discharge transition")
    if np.any(np.diff(v[:k+1]) < -1e-6) or np.any(np.diff(v[k+1:]) > 1e-6):
        raise ValueError("nonmonotonic voltage stage; inspect protocol manually")
    frames = []
    for stage, sl in (("charge", slice(None,k+1)), ("discharge",slice(k+1,None))):
        ts = t[sl]
        frames.append(pd.DataFrame({"cycle_time_h":ts,"time_h":ts-ts[0],
                                    "voltage_v":v[sl],"stage":stage,"rate":20}))
    meta = {"sha256":hashlib.sha256(raw).hexdigest(),"source_header":header,
            "rows":len(t),"charge_duration_h":float(t[k]-t[0]),
            "discharge_duration_h":float(t[-1]-t[k+1]),
            "initial_voltage_v":float(v[0]),"peak_voltage_v":float(v[k]),
            "final_voltage_v":float(v[-1]),"switch_drop_mv":float(1000*(v[k]-v[k+1])),
            "last_sample_is_2p7v":bool(abs(v[-1]-2.7)<1e-4),
            "reference_kind":"comsol_simulation_unmatched_parameters"}
    return pd.concat(frames,ignore_index=True),meta


def compare_cycle(reference, model):
    """Compare stage-local absolute time on reference samples, no extrapolation.

    Model discharge must inherit its own charge end state. Durations are
    separately reported; the observed COMSOL final sample need not be a cutoff.
    """
    rows=[]
    for stage in ("charge","discharge"):
        r=reference[reference.stage==stage]
        m=model[stage]
        t=r.time_h.to_numpy(float)
        end=min(t[-1],float(m.time_h.iloc[-1]))
        if end <= 0: raise ValueError("no common stage interval")
        keep=t<=end+1e-10
        err=np.interp(t[keep],m.time_h,m.voltage_v)-r.voltage_v.to_numpy(float)[keep]
        rows.append(dict(stage=stage,rmse_mv=1000*np.sqrt(np.mean(err**2)),
            mae_mv=1000*np.mean(abs(err)),bias_mv=1000*np.mean(err),
            max_mv=1000*np.max(abs(err)),rmse_exclude_t0_mv=1000*np.sqrt(np.mean(err[1:]**2)),
            model_duration_h=float(m.time_h.iloc[-1]),ref_duration_h=float(t[-1]),
            coverage_pct=100*end/t[-1],model_v0=float(m.voltage_v.iloc[0]),
            model_vend=float(m.voltage_v.iloc[-1]),soc0=float(m.cell_soc.iloc[0]),
            soc_end=float(m.cell_soc.iloc[-1])))
    return rows
