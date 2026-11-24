import numpy as np
import pytest
from solid_pinn.rate_diagnostic import fit_nonnegative_asr

def test_known_asr():
    j=np.array([-2.,-1.,1.,2.])
    fitted,raw=fit_nonnegative_asr(j*.05,j)
    assert fitted==pytest.approx(.05)
    assert raw==pytest.approx(.05)

def test_negative_asr_rejected():
    j=np.array([-1.,1.])
    assert fit_nonnegative_asr(-.2*j,j)==pytest.approx((0.,-.2))

@pytest.mark.parametrize("e,j",[([1],[0]),([1,2],[1]),([np.nan],[1])])
def test_invalid_inputs(e,j):
    with pytest.raises(ValueError):
        fit_nonnegative_asr(e,j)
