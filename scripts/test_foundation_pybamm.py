"""Requires installed pinned PyBaMM; no mock solver."""
import numpy as np
from canonical_fv import Params
from foundation_pybamm import stage,healthy


def test_native_sequential_cycle():
    prev=None
    for kind in ('charge','rest','discharge'):
        row,prev=stage(Params(),8,24,5,kind,150.,1e-8,prev)
        assert healthy(row),row
        assert row['native_samples']>1
        assert np.isfinite(row['voltage']).all()
