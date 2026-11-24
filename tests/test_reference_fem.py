import numpy as np
import pytest
from solid_pinn.reference_fem import ReferenceFEM, matrices


def test_galerkin_weights_and_constant_nullspace():
    for spherical in (False, True):
        _, m, k = matrices(6, spherical)
        np.testing.assert_allclose(k @ np.ones(7), 0, atol=1e-13)
        assert m.sum() == pytest.approx(1/3 if spherical else 1)


@pytest.mark.parametrize("stage,sign",[("charge",-1),("discharge",1)])
def test_independent_axial_current_and_equilibrium(stage,sign):
    ref=ReferenceFEM(nx=4,nr=6)
    I=sign*ref.p.current_a(20)
    field=ref.fields(np.full(len(ref.x),.5),I,stage)
    assert ref.aL*(ref.wx@field.reaction) == pytest.approx(I/ref.p.area_m2,abs=1e-10)
    equilibrium=ref.fields(np.full(len(ref.x),.5),0,stage)
    assert equilibrium.voltage == pytest.approx(float(ref.ocv(.5,stage)),abs=1e-10)
    np.testing.assert_allclose(equilibrium.reaction,0,atol=1e-10)


def test_radial_operator_conserves_lithium():
    ref=ReferenceFEM(nx=4,nr=6)
    np.testing.assert_allclose(ref.wr@ref.radial,0,atol=1e-10)
    expected=3/(ref.p.faraday_c_mol*ref.p.particle_radius_m*ref.p.max_solid_concentration_mol_m3)
    assert ref.wr@ref.flux == pytest.approx(expected)
