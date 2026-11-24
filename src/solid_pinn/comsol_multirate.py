"""Read the collaborator's wide global COMSOL time/voltage/current exports."""
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd


def load_wide_cycle(path, rate, expected_current_a, atol=1e-10):
    """Return sequential stage curves, without averaging switching-event values.

    COMSOL Icell is positive on charge; SOLiD-PINN uses positive discharge.
    The 45 spatial rows in the supplied exports are repeated global values,
    not independent field measurements. Validate every row before reducing.
    """
    if rate not in (5, 10, 20) or not np.isfinite(expected_current_a) or expected_current_a <= 0:
        raise ValueError("invalid rate or expected current")
    path = Path(path)
    with path.open(encoding="utf-8-sig") as stream:
        header = [stream.readline() for _ in range(8)]
    if not all(k in header[-1] for k in ("t (h)", "phis0 (V)", "Icell (A)")):
        raise ValueError("unexpected COMSOL export columns")
    a = np.loadtxt(path, comments="%", ndmin=2)
    if a.shape[1] < 19 or (a.shape[1]-1) % 3 or not np.isfinite(a).all():
        raise ValueError("invalid coordinate + time/voltage/current triples")
    triples = a[:, 1:].reshape(len(a), -1, 3)
    if not np.allclose(triples, triples[:1], rtol=0, atol=atol):
        raise ValueError("global values differ across spatial rows")
    t, v, i = triples[0].T
    if abs(t[0]) > atol or np.any(np.diff(t) < -atol):
        raise ValueError("invalid cycle time")
    if not np.allclose(abs(i), expected_current_a, rtol=1e-6, atol=1e-12):
        raise ValueError("current magnitude mismatch")
    switches = np.flatnonzero(np.sign(i[1:]) != np.sign(i[:-1]))
    if len(switches) != 1:
        raise ValueError("expected one charge/discharge switch")
    k = int(switches[0])
    if k < 2 or k >= len(t)-3 or i[k] <= 0 or i[k+1] >= 0:
        raise ValueError("invalid current sequence")
    if abs(t[k+1]-t[k]) > atol:
        raise ValueError("switch event sides must share time")
    frames = []
    for stage, sl in (("charge",slice(None,k+1)),("discharge",slice(k+1,None))):
        ts=t[sl]
        if np.any(np.diff(ts)<=0):
            raise ValueError("duplicate or reversed time within stage")
        frames.append(pd.DataFrame(dict(cycle_time_h=ts,time_h=ts-ts[0],voltage_v=v[sl],
             current_comsol_a=i[sl],current_a=-i[sl],stage=stage,rate=rate)))
    meta = dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),spatial_rows=len(a),
        time_points=len(t),current_a=expected_current_a,charge_duration_h=float(t[k]),
        discharge_duration_h=float(t[-1]-t[k+1]),switch_drop_mv=float(1000*(v[k]-v[k+1])),
        final_voltage_v=float(v[-1]),last_sample_is_2p7v=bool(abs(v[-1]-2.7)<1e-4))
    return pd.concat(frames,ignore_index=True),meta
