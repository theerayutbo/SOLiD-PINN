import numpy as np
from missing_physics import design,missing,rates,simulate,fit,observe

def test_reference():
    for name in ('null','rest','peak'):
        for j in design().values():
            x=simulate(j,'oracle',[.1,.7,.06,1],name)
            np.testing.assert_allclose(x,simulate(j,'oracle',[.1,.7,.06,1],name,True),atol=2e-6,rtol=0)
            assert x.min()>=0 and x.max()<=1

def test_null_equivalence():
    j=design()['recovery'];p=[.1,.7,.06]
    np.testing.assert_array_equal(simulate(j,'nominal',p,'null'),simulate(j,'oracle',p+[1.],'null'))

def test_missing_recovery():
    j=design()['recovery'];p=[.1,.7,.06];a=simulate(j,'nominal',p,'rest');b=simulate(j,'oracle',p+[1.],'rest')
    assert b[18,0]<a[18,0]
    assert np.all(observe(j,b)[j==0]==0)

def test_positive_closure():
    d=rates('hybrid_rbf',[.1,.7,.06,.1,.02,.03,.04],'rest',np.linspace(0,4,101))[2]
    assert d.min()>=0

def test_oracle_noiseless():
    j=design()['train'];p=[.1,.7,.06,1.];y=observe(j,simulate(j,'oracle',p,'rest',True));q,ok,_=fit('oracle','rest',j,y)
    assert ok;np.testing.assert_allclose(q,p,atol=1e-4,rtol=0)
