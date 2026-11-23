import numpy as np
import pytest
from solid_pinn.numerical import ReducedP2D
from solid_pinn.parameters import Parameters


def test_mass_conservation_radial_diffusion_zero_surface_flux():
    model=ReducedP2D(nx=3,nr=8)
    c=np.linspace(1e3,4e4,model.nr)[None,:]*np.ones((model.nx,1))
    final=model._diffusion_step(c,np.zeros(model.nx),dt_s=120)
    initial_mass=c@model.shell_volumes
    final_mass=final@model.shell_volumes
    np.testing.assert_allclose(initial_mass,final_mass,rtol=1e-10)


def test_particle_surface_flux_matches_total_lithium_balance():
    m=ReducedP2D(nx=3,nr=8)
    c=np.ones((m.nx,m.nr))*10000
    j=np.array([0.1,0.2,0.3])
    dt=60
    next_c=m._diffusion_step(c,j,dt)
    lhs=(next_c-c)@m.shell_volumes
    rhs=dt*j/m.p.faraday_c_mol*m.p.particle_radius_m**2
    np.testing.assert_allclose(lhs,rhs,rtol=1e-8,atol=1e-18)


def test_current_conservation_in_solved_cathode():
    model=ReducedP2D(nx=4,nr=5)
    c=np.ones(model.nx)*0.9*model.p.max_solid_concentration_mol_m3
    i=model.p.current_a(20)
    sol=model.solve_potentials(c, i,"discharge")
    j_geo=model.p.active_surface_area_m_inv*model.dx*sum(sol.reaction_current_a_m2)
    assert j_geo==pytest.approx(i/model.p.area_m2,rel=1e-5)
    assert np.isfinite(sol.cathode_voltage_v)


def test_cycle_smoke():
    model=ReducedP2D(nx=3,nr=5)
    result=model.simulate_cycle(c_rate_denominator=20,dt_s=1800)
    assert set(result.stage.unique()) == {"charge", "discharge"}
    assert np.isfinite(result.voltage_v).all()
    assert len(result)>5
