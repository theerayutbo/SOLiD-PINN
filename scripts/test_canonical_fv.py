from dataclasses import replace
import numpy as np
import pytest
from canonical_fv import Params,Solver

def test_inventory_independent_of_rate_convention():
    p=Params();q=replace(p,qnom=200.)
    assert p.mass_g==q.mass_g and p.inventory==q.inventory
    assert q.current_density(20)>p.current_density(20)
    with pytest.raises(ValueError):Solver(replace(p,eps=.5))

def test_zero_current_and_uniform_state():
    s=Solver();v,q,theta,e=s.fields(np.full((s.n,s.m),.5),0.)
    assert abs(v-3.45)<1e-12 and max(abs(q))<1e-12 and e<1e-12
    np.testing.assert_allclose(s.L@np.ones(s.m),0,atol=1e-12)
    np.testing.assert_allclose(s.w@s.L,0,atol=1e-12)

def test_current_and_particle_flux():
    s=Solver();p=s.p
    for J in (-1.,1.):
        _,q,_,err=s.fields(np.full((s.n,s.m),.5),J)
        assert abs(q.sum()-J)<1e-10 and err<1e-10
        assert abs((q[:,None]*s.b@s.w).mean()*p.F*p.cmax*p.eps*p.L-J)<1e-10

def test_rate_capability():
    s=Solver(nx=3,nr=8)
    for stage in ('charge','discharge'):
        a,_=s.stage(20,stage,step=600.);b,_=s.stage(5,stage,step=600.)
        assert a['termination']==b['termination']=='voltage'
        assert a['capacity']>b['capacity']>0
        assert max(a['mass_residual_C_m2'],b['mass_residual_C_m2'])<1e-5
