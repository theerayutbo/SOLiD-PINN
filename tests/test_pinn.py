import pytest

torch=pytest.importorskip("torch")
from solid_pinn.pinn import invert_sse_conductivity_synthetic


def test_inverse_conductivity_is_learnable_from_synthetic_potential():
    r=invert_sse_conductivity_synthetic(epochs=450,collocation_points=16)
    assert r.relative_error<0.15


def test_ohmic_forward_model_uses_physical_current_and_length():
    import numpy as np
    from solid_pinn.pinn import ohmic_potential_v

    x = np.array([0.0, 0.5, 1.0])
    phi = ohmic_potential_v(x, 1.0, 725e-6, 0.43)
    assert phi[0] == pytest.approx(0.0)
    assert phi[-1] == pytest.approx(-1.0 * 725e-6 / 0.43)
    np.testing.assert_allclose(
        ohmic_potential_v(x, 2.0, 725e-6, 0.43), 2 * phi
    )
    np.testing.assert_allclose(
        ohmic_potential_v(x, 1.0, 2 * 725e-6, 0.43), 2 * phi
    )
    with pytest.raises(ValueError):
        ohmic_potential_v(x, 1.0, 725e-6, -0.43)


def test_synthetic_inversion_tracks_dimensionful_observed_voltage():
    a = invert_sse_conductivity_synthetic(
        epochs=2, seed=7, noise_fraction=0.0,
        current_density=1.0, separator_length_m=725e-6
    )
    b = invert_sse_conductivity_synthetic(
        epochs=2, seed=7, noise_fraction=0.0,
        current_density=2.0, separator_length_m=725e-6
    )
    assert b.reference_voltage_v == pytest.approx(2 * a.reference_voltage_v)
    assert b.observed_drop_v == pytest.approx(2 * a.observed_drop_v)
    assert a.observed_drop_v == pytest.approx(725e-6 / 0.43)
    with pytest.raises(ValueError, match="noise_fraction"):
        invert_sse_conductivity_synthetic(noise_fraction=-0.1)
