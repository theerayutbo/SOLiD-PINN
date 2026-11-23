"""Independent analytical spherical-diffusion verification.

A radial Neumann eigenmode solves the 3D spherical diffusion PDE exactly:
c(r,t) = c_bar + A * sinc(k*r) * exp(-D*k^2*t)
where tan(k*R) = k*R. The volume-average of each finite-volume shell is
compared to the analytical shell average (not a point sample).
"""

import numpy as np

from solid_pinn.numerical import ReducedP2D

# First positive root of tan(z) = z (Neumann sphere radial eigenmode).
NEUMANN_LAMBDA = 4.493409457909064
BACKGROUND = 20000.0
AMPLITUDE = 3000.0


def _analytical_shell_means(model: ReducedP2D, time_s: float) -> np.ndarray:
    radius = model.p.particle_radius_m
    wave_number = NEUMANN_LAMBDA / radius
    z = wave_number * model.rfaces
    # Primitive: integral r^2 * sin(k*r)/(k*r) dr.
    primitive = (np.sin(z) - z * np.cos(z)) / wave_number**3
    shell_mean = 3 * np.diff(primitive) / np.diff(model.rfaces**3)
    decay = np.exp(-model.p.particle_diffusivity_m2_s * wave_number**2 * time_s)
    return BACKGROUND + AMPLITUDE * shell_mean * decay


def _integrate(model: ReducedP2D, dt_s: float, duration_s: float) -> np.ndarray:
    n = round(duration_s / dt_s)
    assert np.isclose(n * dt_s, duration_s)
    initial = _analytical_shell_means(model, 0.0)
    concentration = np.tile(initial, (model.nx, 1))
    for _ in range(n):
        concentration = model._diffusion_step(concentration, np.zeros(model.nx), dt_s)
    return concentration[0]


def test_spherical_diffusion_spatial_convergence_against_analytic_mode():
    errors = []
    for nr in (6, 12, 24):
        model = ReducedP2D(nx=2, nr=nr)
        calculated = _integrate(model, dt_s=0.1, duration_s=12.0)
        expected = _analytical_shell_means(model, time_s=12.0)
        errors.append(np.sqrt(np.mean((calculated - expected) ** 2)) / AMPLITUDE)

    assert errors[2] < errors[1] < errors[0]
    assert errors[2] < 0.02


def test_spherical_diffusion_time_convergence_against_analytic_mode():
    model = ReducedP2D(nx=2, nr=24)
    expected = _analytical_shell_means(model, time_s=12.0)
    errors = []
    for dt_s in (1.0, 0.2):
        calculated = _integrate(model, dt_s=dt_s, duration_s=12.0)
        errors.append(np.sqrt(np.mean((calculated - expected) ** 2)))
    assert errors[1] < errors[0]
