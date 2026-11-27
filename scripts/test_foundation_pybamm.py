"""Requires installed pinned PyBaMM; no mock solver."""
import numpy as np
import pytest
from canonical_fv import Params
from foundation_pybamm import stage,healthy


@pytest.mark.parametrize('rate,nx,nr,step,rtol',[(5,8,24,150.,1e-8),(5,16,48,75.,1e-9),(10,16,48,150.,1e-8),(20,16,48,150.,1e-8)])
def test_native_sequential_cycle(rate,nx,nr,step,rtol):
    prev=None
    for kind in ('charge','rest','discharge'):
        row,prev=stage(Params(),nx,nr,rate,kind,step,rtol,prev)
        diagnostic={k:v for k,v in row.items() if not isinstance(v,list)}
        print('NATIVE_STAGE',diagnostic,flush=True)
        assert healthy(row),repr(diagnostic)
        assert row['native_samples']>1
        assert np.isfinite(row['voltage']).all()
