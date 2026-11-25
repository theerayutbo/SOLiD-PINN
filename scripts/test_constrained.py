import json
import numpy as np
from constrained import law,rate_fn,validation,profiles,observe,reference,nodal_fit,fit,LEVELS,rmse

def test_monotone_and_positive():
    grid=np.linspace(0,4,201)
    for seed in range(5):
        p=np.random.default_rng(seed).normal(size=10)
        a=rate_fn('monotone',p)(grid)
        assert a[0]==0 and np.all(np.diff(a)>=0)
        assert np.min(rate_fn('free',p)(grid))>=0

def test_peak_not_monotone():
    a=law('peak',np.linspace(0,4,201))
    assert a[0]==0 and a.min()>=0 and np.min(np.diff(a))<0

def test_profile_separation():
    vals=lambda j:set(np.unique(abs(j)))-{0}
    assert not vals(validation())&vals(profiles('train'))
    assert not vals(validation())&vals(profiles('interp'))
    assert not vals(validation())&vals(profiles('extra'))

def test_nodal_fit_noise_free():
    j=profiles('train');r=lambda j:law('rational',j);y=observe(j,reference(j,r))
    f=nodal_fit(j,y);np.testing.assert_allclose(f.x,r(LEVELS[1:]),atol=1e-6,rtol=0)

def test_rate_fit_finite():
    j=profiles('train');r=lambda j:law('rational',j);f=nodal_fit(j,observe(j,reference(j,r)))
    g=fit('monotone',f,101,20.)
    assert g.success and np.all(np.isfinite(g.x))
