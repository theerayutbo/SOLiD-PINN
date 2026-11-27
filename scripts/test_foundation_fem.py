import numpy as np
from canonical_fv import Params,Solver
from foundation_fem import FEM,matrices
from verify_foundation import cycle,compare


def test_galerkin_operators():
    p=Params();M,K=matrices(8,p.R,True)
    np.testing.assert_allclose(M.sum(),p.R**3/3,rtol=1e-12,atol=0)
    np.testing.assert_allclose(K@np.ones(9),0,atol=1e-18)
    assert np.min(np.linalg.eigvalsh(M))>0


def test_uniform_rest():
    s=FEM();c=np.full((s.n,s.m),.5);v,q,_,err=s.fields(c,0.)
    assert abs(v-3.45)<1e-12 and max(abs(q))<1e-12 and err<1e-12
    assert np.max(abs(s.rhs(c,q)))<1e-12


def test_signed_mass():
    s=FEM();p=s.p;c=np.full((s.n,s.m),.5)
    for J in (-1.,1.):
        _,q,_,_=s.fields(c,J)
        assert abs(q.sum()-J)<1e-10
        assert abs(s.mean(s.rhs(c,q))*p.F*p.cmax*p.eps*p.L-J)<1e-10


def test_sequential_cross_solver():
    a=cycle(Solver(nx=8,nr=24),5,150.,1e-8);b=cycle(FEM(nx=8,nr=24),5,150.,1e-8)
    for rows in (a,b):
        assert [x['termination'] for x in rows]==['voltage','rest_complete','voltage']
        assert abs(rows[0]['end_mean']-rows[1]['start_mean'])<1e-12
        assert abs(rows[1]['end_mean']-rows[2]['start_mean'])<1e-12
        assert all(x['mass_residual']<1e-5 and 0<x['min_theta']<=x['max_theta']<1 for x in rows)
    for u,v in zip(a,b):
        d=compare(u,v);assert d['max_voltage_mv']<1 and d['capacity_delta_pct']<.5
