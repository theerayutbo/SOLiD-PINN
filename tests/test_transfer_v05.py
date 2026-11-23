import numpy as np
import pytest
from solid_pinn.numerical import ReducedP2D
from solid_pinn.parameters import Parameters
from solid_pinn.transfer import (
    SeriesInterfaceReducedP2D, conductivity_activation_j_mol, temperature_scenario
)


def test_series_asr_fixed_state_exact_ohmic_loss():
    p = Parameters()
    baseline = ReducedP2D(p, nx=3, nr=5)
    modified = SeriesInterfaceReducedP2D(p, nx=3, nr=5, interface_asr_ohm_m2=0.02)
    c = np.full(3, 0.7 * p.max_solid_concentration_mol_m3)
    for stage, sign in (("charge", -1), ("discharge", 1)):
        current_a = sign * p.current_a(20)
        old = baseline.solve_potentials(c, current_a, stage)
        new = modified.solve_potentials(c, current_a, stage)
        assert new.cathode_voltage_v - old.cathode_voltage_v == pytest.approx(
            -current_a / p.area_m2 * 0.02, abs=1e-7
        )
        np.testing.assert_allclose(
            new.reaction_current_a_m2, old.reaction_current_a_m2, atol=1e-8
        )


def test_paper_arrhenius_conductivities_and_opt_in_diffusion():
    p = Parameters()
    assert conductivity_activation_j_mol() == pytest.approx(31676.310887882737)
    assert temperature_scenario(p, 298.15).kappa_sse_s_m == pytest.approx(0.16)
    assert temperature_scenario(p, 323.15).kappa_sse_s_m == pytest.approx(0.43)
    assert temperature_scenario(p, 298.15).particle_diffusivity_m2_s == p.particle_diffusivity_m2_s
    assert temperature_scenario(
        p, 298.15, diffusion_ea_j_mol=25000
    ).particle_diffusivity_m2_s < p.particle_diffusivity_m2_s


def test_invalid_values_rejected():
    with pytest.raises(ValueError):
        SeriesInterfaceReducedP2D(interface_asr_ohm_m2=-1)
    with pytest.raises(ValueError):
        temperature_scenario(Parameters(), float("nan"))
    with pytest.raises(ValueError):
        temperature_scenario(Parameters(), 298.15, diffusion_ea_j_mol=-1)
