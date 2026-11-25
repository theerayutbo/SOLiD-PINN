import numpy as np
from mesh_bridge import cell,profile

def test_modal_reference():
    j=profile('test');a,_=cell(j,4,6);b,_=cell(j,4,6,True)
    np.testing.assert_allclose(a,b,atol=1e-8,rtol=0)

def test_conservation_and_surface():
    for k in ('train','test','extra'):
        _,a=cell(profile(k),16,24)
        assert a['mass']<1e-9 and a['charge']<1e-9
        assert 0<a['min_c']<=a['max_c']<1 and 0<a['min_surface']<=a['max_surface']<1

def test_mesh_gate():
    for k in ('train','test','extra'):
        j=profile(k);a,_=cell(j,32,48);b,_=cell(j,64,96)
        assert np.max(abs(a-b))*1000<=1

def test_zero_current():
    v,a=cell(np.zeros((5,1)),8,12)
    np.testing.assert_allclose(v,3.7,atol=1e-10,rtol=0)
    assert a['mass']<1e-9
