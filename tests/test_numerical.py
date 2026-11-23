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


def test_cutoff_time_is_refined_inside_step(monkeypatch):
    """A synthetic linear voltage ramp crosses the 4.2 V limit after 60 s."""
    from solid_pinn.numerical import ElectrochemicalSolution
    from solid_pinn.validation import capacity_ah

    model = ReducedP2D(nx=3, nr=5)
    baseline = 0.5 * model.p.max_solid_concentration_mol_m3
    c0 = np.full((model.nx, model.nr), baseline)

    def fake_solve(surface_c, current_a, stage):
        voltage = 3.0 + 0.02 * (surface_c[0] - baseline)
        return ElectrochemicalSolution(
            voltage, np.zeros(model.nx), np.zeros(model.nx),
            np.zeros(model.nx), True
        )

    def fake_step(c, j, dt_s):
        return c + dt_s

    monkeypatch.setattr(model, "solve_potentials", fake_solve)
    monkeypatch.setattr(model, "_diffusion_step", fake_step)

    curve, end_c = model.simulate_stage(
        "charge", c0=c0, c_rate_denominator=20, dt_s=120, max_hours=1
    )
    np.testing.assert_allclose(curve.time_h.iloc[-1] * 3600, 60, atol=1e-5)
    assert curve.voltage_v.iloc[-1] == pytest.approx(4.2, abs=1e-7)
    assert end_c[0, 0] == pytest.approx(baseline + 60, abs=1e-5)
    assert capacity_ah(curve, "charge") == pytest.approx(
        model.p.current_a(20) * 60 / 3600, rel=1e-7
    )


def test_invalid_integration_settings_are_rejected():
    model = ReducedP2D(nx=3, nr=5)
    with pytest.raises(ValueError, match="dt_s"):
        model.simulate_stage("charge", dt_s=float("nan"))
    with pytest.raises(ValueError, match="max_hours"):
        model.simulate_stage("charge", max_hours=0)
