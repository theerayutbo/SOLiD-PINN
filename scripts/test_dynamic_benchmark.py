import numpy as np
from dynamic_benchmark import profiles,true_rate,reference,integrate,observe,rate_fn

def test_reference_and_bounds():
    for name in ('rational','exponential'):
        for group in ('train','interp','extra','history'):
            j=profiles(group);r=lambda x:true_rate(name,x);x=integrate(j,r)
            np.testing.assert_allclose(x,reference(j,r),atol=1e-6,rtol=0)
            assert np.min(x)>=0 and np.max(x)<=1

def test_history_and_rest():
    j=profiles('history');r=lambda x:true_rate('rational',x);x=integrate(j,r);v=observe(j,x)
    assert j[24,0]==j[24,1] and abs(v[24,0]-v[24,1])>1
    assert np.all(v[j==0]==0)
    assert abs(observe(j,integrate(j,r,static=True))[24,0]-observe(j,integrate(j,r,static=True))[24,1])<1e-12

def test_neural_rate_nonnegative():
    r=rate_fn('neural_ode',np.arange(10.)/10,'rational');a=r(np.array([0.,.5,1.,2.,4.]))
    assert a[0]==0 and np.all(a[1:]>0)

def test_disjoint_nonzero_amplitudes():
    tr=set(np.unique(abs(profiles('train'))))-{0};te=set(np.unique(abs(profiles('interp'))))-{0}
    assert not tr&te
