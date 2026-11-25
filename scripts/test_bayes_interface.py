import numpy as np
from bayes_interface import P,LO,HI,K,design,voltage,weights,posterior

def test_trapezoid():
    x=np.array([0.,.1,.4,2.]);assert np.isclose(weights(x).sum(),2.)

def test_single_current_ridge():
    t,j=design('single');p=P.copy();p[3]=1.2;p[:2]+=K*(np.arcsinh(1/(2*P[3]))-np.arcsinh(1/(2*p[3])))/2
    np.testing.assert_allclose(voltage(t,j,p),voltage(t,j,P),atol=1e-10)

def test_posterior_bounds_and_multicurrent():
    t,j=design('multi');p,m=posterior(t,j,voltage(t,j,P),1.,n=101,draws=4000)
    assert np.all((p>=LO)&(p<=HI));np.testing.assert_allclose(np.median(p,axis=0),P,rtol=.02)
    assert np.ptp(np.array(m['quantiles'])[[0,2],3])<.02
