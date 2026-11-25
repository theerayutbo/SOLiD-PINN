import numpy as np
from hybrid_p2d import cell,profile,closure,voltage,fit

def test_conservation():
    for k in ('train','test','extra'):
        _,a=cell(profile(k));assert a['mass']<1e-10 and a['charge']<1e-10 and 0<a['min_c']<=a['max_c']<1

def test_reference():
    j=profile('test');a,_=cell(j);b,_=cell(j,reference=True);np.testing.assert_allclose(a,b,atol=1e-10,rtol=0)

def test_closure_bounds_and_rest():
    j=np.array([[2.],[2.],[0.],[0.],[0.]])
    x=closure(j,'oracle',[.35,.7,1.],'rest');assert x[0,0]==0 and x[2,0]>x[-1,0] and np.all((x>=0)&(x<=1))

def test_noise_free_oracle():
    j=profile('train');b,_=cell(j);y=voltage(b,j,'oracle',[.35,.7,1.],'rest');f=fit(b,j,y,'oracle','rest');assert f.success;np.testing.assert_allclose(f.x,[.35,.7,1.],atol=1e-6,rtol=0)
