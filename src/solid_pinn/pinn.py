"""Physics-informed inverse problem for Li6PS5Cl ionic conductivity (Eq. 10).

This is a real PINN for the *electrolyte subsystem*, not an end-to-end
P2D PINN. Synthetic potential measurements demonstrate identifiability.
For experimental inversion, supply measured potential fields or equivalent
observables with an appropriate forward operator.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class InverseResult:
    estimated_conductivity_s_m: float
    true_conductivity_s_m: float
    relative_error: float
    final_total_loss: float
    epochs: int
    reference_voltage_v: float
    observed_drop_v: float


def ohmic_potential_v(
    x_normalized: np.ndarray | float,
    current_density_a_m2: float,
    separator_length_m: float,
    conductivity_s_m: float,
) -> np.ndarray:
    """Analytical 1D SSE potential relative to phi(0)=0, in SI volts."""
    physical = (current_density_a_m2, separator_length_m, conductivity_s_m)
    if not all(np.isfinite(v) and v > 0 for v in physical):
        raise ValueError("J, L and conductivity must be finite and strictly positive")
    x = np.asarray(x_normalized, dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("Coordinates must be finite")
    return -current_density_a_m2 * separator_length_m * x / conductivity_s_m


def invert_sse_conductivity_synthetic(
    true_kappa: float = 0.43,
    initial_kappa: float = 0.20,
    current_density: float = 1.0,
    separator_length_m: float = 725e-6,
    epochs: int = 900,
    seed: int = 42,
    noise_fraction: float = 0.0,
    collocation_points: int = 32,
) -> InverseResult:
    """Fit kappa from synthetic phi(x) under div(kappa grad(phi))=0.

    The PINN observes a sparse field and uses physics + flux boundary loss.
    All of its training and evaluation data are synthetic by construction.
    """
    try:
        import torch
    except ImportError as exc:
        raise ImportError("Install the optional 'pinn' dependency: pip install -e '.[pinn]'") from exc

    physical = (true_kappa, initial_kappa, current_density, separator_length_m)
    if not all(np.isfinite(v) and v > 0 for v in physical):
        raise ValueError("All physical parameters must be finite and positive")
    if not np.isfinite(noise_fraction) or noise_fraction < 0:
        raise ValueError("noise_fraction must be nonnegative and finite")
    if epochs < 1 or collocation_points < 3:
        raise ValueError("epochs >= 1; collocation_points >= 3")
    torch.manual_seed(seed)
    torch.set_num_threads(min(torch.get_num_threads(), 2))
    dtype = torch.float64
    kappa_prior = initial_kappa

    class Net(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.net = torch.nn.Sequential(
                torch.nn.Linear(1, 24), torch.nn.Tanh(),
                torch.nn.Linear(24, 24), torch.nn.Tanh(),
                torch.nn.Linear(24, 1),
            )
        def forward(self, x):
            return x*self.net(x)  # hard boundary condition u(0) == 0

    net = Net().to(dtype=dtype)
    log_kappa = torch.nn.Parameter(torch.tensor(float(np.log(initial_kappa)), dtype=dtype))
    optimizer = torch.optim.Adam(list(net.parameters())+[log_kappa],lr=0.005)
    x_data_np = np.linspace(0.05, 1.0, 16)[:,None]
    rng = np.random.default_rng(seed)
    # Construct *physical voltage measurements* first: phi(x) = -J L x/kappa.
    # Normalise by a reference drop only AFTER applying the physical forward law.
    # Relative noise is scaled to this reference; absolute instrument noise can
    # be introduced in a future experimental-inversion interface.
    reference_voltage_v = current_density * separator_length_m / kappa_prior
    phi_obs_v = ohmic_potential_v(
        x_data_np, current_density, separator_length_m, true_kappa
    )
    phi_obs_v += rng.normal(
        0.0, noise_fraction * reference_voltage_v, size=x_data_np.shape
    )
    u_obs = phi_obs_v / reference_voltage_v
    x_obs = torch.tensor(x_data_np,dtype=dtype)
    u_data = torch.tensor(u_obs,dtype=dtype)
    loss_value = float("nan")

    for _ in range(epochs):
        optimizer.zero_grad()
        x = torch.linspace(0,1,collocation_points,dtype=dtype).reshape(-1,1).requires_grad_(True)
        u = net(x)
        ux = torch.autograd.grad(u.sum(),x,create_graph=True)[0]
        uxx = torch.autograd.grad(ux.sum(),x,create_graph=True)[0]
        kappa = torch.exp(log_kappa)
        # dimensionless Ohm's law, constant kappa and zero source.
        pde_loss = torch.mean(uxx**2)
        # i = -kappa dphi/dx_phys = J at x=1; x is dimensionless.
        flux_loss = (-kappa/kappa_prior*ux[-1] - 1.0).pow(2).mean()
        data_loss = torch.mean((net(x_obs)-u_data)**2)
        loss = 0.05*pde_loss + flux_loss + 10.0*data_loss
        loss.backward()
        optimizer.step()
        loss_value = float(loss.detach().item())
    predicted = float(torch.exp(log_kappa).detach().item())
    return InverseResult(
        predicted, true_kappa, abs(predicted-true_kappa)/true_kappa,
        loss_value, epochs, reference_voltage_v, -float(phi_obs_v[-1, 0]),
    )
