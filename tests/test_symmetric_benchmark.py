import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import numpy as np
import pytest
from symmetric_benchmark import condition, predict, fit, analyze


def test_single_amplitude_nonidentifiable():
    assert condition(np.tile([-1.,1.],100)) < 1e-12
    assert condition(np.array([-2.,-1.,-.1,.1,1.,2.])) > .01


def test_passive_relaxation():
    t=np.linspace(0,100,101)
    r=predict('relaxation',[5,2,12],t)
    assert np.all((r>=2)&(r<=5))
    np.testing.assert_allclose(predict('relaxation',fit('relaxation',t,r),t),r,atol=1e-5)


def test_signed_voltage_and_constant():
    p=fit('constant',np.arange(3.),np.array([2.,3.,4.]))
    np.testing.assert_array_equal(2*np.array([-1.,1.])*predict('constant',p,np.array([1.,2.])),[-6.,6.])


def test_hash_guard():
    with pytest.raises(ValueError,match='unexpected ASR export hash'):
        analyze(b'wrong')
