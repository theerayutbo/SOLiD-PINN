import numpy as np
from coupled_bridge import simulate,healthy,profile,TRUE,fit,rmse

def test_conservation_and_passivity():
    for truth in ('null','rest','peak'):
        _,c,_=simulate(profile('test'),'oracle',TRUE,truth,(8,12,2),True)
        assert healthy(c)

def test_reaction_feedback():
    j=profile('test');v,c,p=simulate(j,'oracle',TRUE,'rest',(8,12,2),True)
    w,d,q=simulate(j,'oracle',TRUE,'null',(8,12,2),True)
    assert np.max(abs(v-w))>1e-3 and np.max(abs(p-q))>1e-5
    np.testing.assert_allclose(p.sum(1),q.sum(1),atol=1e-12)

def test_refinement():
    j=profile('test');v,_,_=simulate(j,'oracle',TRUE,'rest',(8,12,2));w,_,_=simulate(j,'oracle',TRUE,'rest',(8,12,4));z,_,_=simulate(j,'oracle',TRUE,'rest',(8,12,8))
    assert np.max(abs(w-z))<np.max(abs(v-w))

def test_oracle_inverse():
    j=profile('train');mesh=(4,6,1);y,_,_=simulate(j,'oracle',TRUE,'rest',mesh);f=fit(j,y,'oracle','rest',mesh)
    assert f.success;np.testing.assert_allclose(f.x,TRUE,rtol=1e-5,atol=1e-5)
