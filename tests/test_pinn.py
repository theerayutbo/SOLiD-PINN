import pytest

torch=pytest.importorskip("torch")
from solid_pinn.pinn import invert_sse_conductivity_synthetic


def test_inverse_conductivity_is_learnable_from_synthetic_potential():
    r=invert_sse_conductivity_synthetic(epochs=450,collocation_points=16)
    assert r.relative_error<0.15
