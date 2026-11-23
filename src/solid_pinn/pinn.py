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

    if min(true_kappa, initial_kappa, current_density, separator_length_m) <= 0:
        raise ValueError("All physical parameters must be positive")
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
    noise = rng.normal(0, noise_fraction, size=x_data_np.shape)
    # True analytical solution: phi(x) = -J L x / kappa.
    u_obs = -(kappa_prior/true_kappa) * x_data_np + noise
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
    return InverseResult(predicted,true_kappa,abs(predicted-true_kappa)/true_kappa,loss_value,epochs)
