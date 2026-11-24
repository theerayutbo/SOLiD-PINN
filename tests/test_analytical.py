import numpy as np
import pytest
from scipy.integrate import trapezoid
from solid_pinn.analytical import (linear_profile, benchmark, corrected_paper_parameters,
    phase_volume_fractions, usable_soc)
from solid_pinn.parameters import Parameters


@pytest.mark.parametrize('kr',[.1,1.,10.])
def test_analytic_boundaries_integral_and_symmetry(kr):
    y=np.linspace(0,1,10001)
    w,q=linear_profile(y,3.,kr)
    assert w[0]==pytest.approx(1)
    assert w[-1]==pytest.approx(0,abs=1e-14)
    assert trapezoid(q,y)==pytest.approx(1,abs=1e-7)
    _,qr=linear_profile(1-y,3.,1/kr)
    np.testing.assert_allclose(q,qr,rtol=1e-13)


def test_uniform_limit():
    y=np.linspace(0,1,10)
    w,q=linear_profile(y,0.,.1)
    np.testing.assert_allclose(w,1-y)
    np.testing.assert_allclose(q,1.)


def test_independent_solver_linear_limit_and_refinement():
    rows=benchmark(meshes=(8,32))
    assert len(rows)==32
    for row in rows:
        if row['nx']==32:
            assert row['max_reaction_error_pct']<.2
        if row['case']!='corrected_baseline' and row['nx']==8:
            fine=next(r for r in rows if r['nx']==32 and all(r[k]==row[k] for k in ('case','solver','stage')))
            assert fine['max_reaction_error_pct']<row['max_reaction_error_pct']


def test_parameter_correction_is_default():
    assert Parameters().sigma_cathode_s_m==.17
    assert corrected_paper_parameters(Parameters(sigma_cathode_s_m=.171)).sigma_cathode_s_m==.17


def test_composition_and_soc_mapping():
    v=phase_volume_fractions([.5,.5],[2.,1.],.1)
    np.testing.assert_allclose(v,[.3,.6])
    np.testing.assert_allclose(usable_soc([.2,.5,.8],.2,.8),[1,.5,0],atol=1e-14)
    with pytest.raises(ValueError): phase_volume_fractions([.5,.4],[2.,1.])
    with pytest.raises(ValueError): usable_soc(.5,.8,.2)
