"""Finite-volume reduced P2D Li|argyrodite|NMC half-cell prototype.

Covers: 1D charge conservation across composite cathode (algebraic), spherical
radial particle diffusion at each axial cell, Li-metal boundary kinetics,
single-ion Ohmic electrolyte, and galvanostatic charge/discharge.

Not a COMSOL equivalent: cathode phase volume fractions, BV exchange currents,
OCV curves, interfacial resistance, collector thickness, etc. need validation.
"""

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
from scipy.linalg import lu_factor, lu_solve
from scipy.optimize import root

from .ocv import ocv_v
from .parameters import Parameters


@dataclass
class ElectrochemicalSolution:
    cathode_voltage_v: float
    reaction_current_a_m2: np.ndarray
    electrolyte_potential_v: np.ndarray
    solid_potential_v: np.ndarray
    solver_success: bool


class ReducedP2D:
    """1D composite cathode + radial spherical FVM (x and r dimensions)."""

    def __init__(
        self, params: Parameters | None = None, nx: int = 6, nr: int = 10,
        ocv_function: Callable[[np.ndarray | float, str], np.ndarray] = ocv_v,
    ):
        if nx < 2 or nr < 3:
            raise ValueError("nx >=2 and nr >=3 are required")
        self.p = params or Parameters()
        self.ocv = ocv_function
        self.nx, self.nr = nx, nr
        self.dx = self.p.cathode_m / nx
        self.dr = self.p.particle_radius_m / nr
        self.rfaces = np.linspace(0, self.p.particle_radius_m, nr + 1)
        self.shell_volumes = (self.rfaces[1:] ** 3 - self.rfaces[:-1] ** 3) / 3.0
        self.diffusion_operator = self._diffusion_matrix()
        self._previous_potential_state: np.ndarray | None = None

    def _diffusion_matrix(self) -> np.ndarray:
        nr = self.nr
        diffusivity = self.p.particle_diffusivity_m2_s
        a = np.zeros((nr, nr))
        for k in range(1, nr):
            coeff = diffusivity * self.rfaces[k] ** 2 / self.dr
            left, right = k - 1, k
            a[left, left] -= coeff / self.shell_volumes[left]
            a[left, right] += coeff / self.shell_volumes[left]
            a[right, left] += coeff / self.shell_volumes[right]
            a[right, right] -= coeff / self.shell_volumes[right]
        return a

    def _initial_guess(self, surface_c: np.ndarray, current_density: float, stage: str) -> np.ndarray:
        p = self.p
        x = (np.arange(self.nx) + 0.5) * self.dx
        j_uniform = current_density / (p.active_surface_area_m_inv * p.cathode_m)
        beta = p.faraday_c_mol / (2 * p.gas_constant_j_mol_k * p.temperature_k)
        eta_li = np.arcsinh(current_density / (2 * p.exchange_current_lithium_a_m2)) / beta
        phi_ref = -eta_li - current_density * p.separator_m / p.kappa_sse_s_m
        i_e = current_density * (1 - x / p.cathode_m)
        phi_e = phi_ref - (current_density * x - current_density * x*x/(2*p.cathode_m)) / p.kappa_cathode_effective
        phi_s = phi_e + self.ocv(1-surface_c/p.max_solid_concentration_mol_m3, stage) - np.arcsinh(j_uniform/(2*p.exchange_current_cathode_a_m2)) / beta
        return np.concatenate([phi_e, phi_s, np.full(self.nx, j_uniform)])

    def solve_potentials(self, surface_c: np.ndarray, current_a: float, stage: str) -> ElectrochemicalSolution:
        p = self.p
        surface_c = np.asarray(surface_c, dtype=float)
        if surface_c.shape != (self.nx,):
            raise ValueError(f"surface concentration must have shape ({self.nx},)")
        J = current_a / p.area_m2  # geometric current density, positive discharge
        kappa = p.kappa_cathode_effective
        sigma = p.sigma_cathode_s_m
        a = p.active_surface_area_m_inv
        beta = p.faraday_c_mol / (2 * p.gas_constant_j_mol_k * p.temperature_k)
        u = self.ocv(1 - surface_c / p.max_solid_concentration_mol_m3, stage)
        eta_li = np.arcsinh(J / (2*p.exchange_current_lithium_a_m2)) / beta
        phi_left = -eta_li - J*p.separator_m/p.kappa_sse_s_m
        n = self.nx

        def residual(z: np.ndarray) -> np.ndarray:
            phi_e = z[:n]
            phi_s = z[n:2*n]
            j = z[2*n:]
            i_e = np.empty(n+1)
            i_s = np.empty(n+1)
            i_e[0], i_e[-1] = J, 0.0
            i_s[0], i_s[-1] = 0.0, J
            i_e[1:-1] = -kappa * np.diff(phi_e) / self.dx
            i_s[1:-1] = -sigma * np.diff(phi_s) / self.dx
            r_e = i_e[:-1] - i_e[1:] - a*j*self.dx
            r_s = i_s[1:-1] - i_s[:-2] - a*j[:-1]*self.dx
            eta = phi_s - phi_e - u
            bv_j = -2*p.exchange_current_cathode_a_m2*np.sinh(np.clip(beta*eta,-25,25))
            r_bv = (j - bv_j) * a*p.cathode_m
            gauge = (phi_e[0] - (phi_left - J*self.dx/(2*kappa))) * kappa / self.dx
            return np.concatenate([r_e, r_s, r_bv, [gauge]])

        initial = self._initial_guess(surface_c, J, stage)
        sol = root(residual, initial, method="hybr", options={"xtol": 1e-9})
        norm = np.linalg.norm(residual(sol.x), ord=np.inf)
        if not np.isfinite(norm) or norm > 1e-5:
            raise RuntimeError(f"Electrochemical nonlinear solve failed: {sol.message}; residual {norm:.3g}")
        pe, ps, j = sol.x[:n], sol.x[n:2*n], sol.x[2*n:]
        v = float(ps[-1] - J*self.dx/(2*sigma))  # collector-face potential
        return ElectrochemicalSolution(v, j, pe, ps, bool(sol.success))

    def _diffusion_step(self, c: np.ndarray, j: np.ndarray, dt_s: float) -> np.ndarray:
        """Implicit Euler, FV, mass conserving radial flux boundary."""
        rhs = c.copy()
        rhs[:, -1] += dt_s * (
            j / self.p.faraday_c_mol
            * self.rfaces[-1]**2 / self.shell_volumes[-1]
        )
        lu, piv = lu_factor(np.eye(self.nr) - dt_s * self.diffusion_operator)
        return lu_solve((lu, piv), rhs.T).T

    def _state_of_charge(self, c: np.ndarray) -> float:
        """Volume-weighted mean particle SoC over all axial cells."""
        mean_c = float(np.mean(c @ self.shell_volumes / np.sum(self.shell_volumes)))
        return 1.0 - mean_c / self.p.max_solid_concentration_mol_m3

    def _cutoff_margin(self, stage: str, voltage_v: float, soc: float) -> float:
        """Positive inside the operating region; zero at the first active cutoff."""
        if stage == "charge":
            return min(self.p.upper_cutoff_v - voltage_v, 0.995 - soc)
        return min(voltage_v - self.p.lower_cutoff_v, soc - 0.005)

    def _refine_terminal_step(
        self,
        c_start: np.ndarray,
        sol_start: ElectrochemicalSolution,
        current_a: float,
        stage: str,
        interval_s: float,
        iterations: int = 32,
    ) -> tuple[float, np.ndarray, ElectrochemicalSolution]:
        """Locate a cutoff within a time step, using the same frozen reaction
        flux and implicit radial diffusion update as the outer integrator.

        This removes the O(dt) endpoint quantisation of capacity. It does NOT
        remove the time integration error; convergence studies remain essential.
        """
        low, high = 0.0, interval_s
        for _ in range(iterations):
            mid = 0.5 * (low + high)
            candidate = self._diffusion_step(
                c_start, sol_start.reaction_current_a_m2, mid
            )
            candidate_sol = self.solve_potentials(candidate[:, -1], current_a, stage)
            if self._cutoff_margin(
                stage, candidate_sol.cathode_voltage_v, self._state_of_charge(candidate)
            ) <= 0:
                high = mid
            else:
                low = mid
        c_end = self._diffusion_step(
            c_start, sol_start.reaction_current_a_m2, high
        )
        sol_end = self.solve_potentials(c_end[:, -1], current_a, stage)
        return high, c_end, sol_end

    def simulate_stage(
        self, stage: str, c0: np.ndarray | None = None,
        c_rate_denominator: int = 20, dt_s: float = 300.0,
        max_hours: float | None = None,
    ) -> tuple[pd.DataFrame, np.ndarray]:
        if stage not in {"charge", "discharge"}:
            raise ValueError("stage must be charge or discharge")
        if not np.isfinite(dt_s) or dt_s <= 0:
            raise ValueError("dt_s must be a positive finite number")
        if max_hours is not None and (not np.isfinite(max_hours) or max_hours <= 0):
            raise ValueError("max_hours must be a positive finite number")
        p = self.p
        if c0 is None:
            c = np.full((self.nx, self.nr), (1-p.initial_soc)*p.max_solid_concentration_mol_m3)
        else:
            c = np.asarray(c0, dtype=float).copy()
            if c.shape != (self.nx, self.nr):
                raise ValueError("c0 shape mismatch")
        current = p.current_a(c_rate_denominator) * (-1 if stage == "charge" else 1)
        max_t = 3600 * (max_hours if max_hours is not None else c_rate_denominator * 1.25)
        rows: list[dict] = []
        time_s = 0.0
        sol = self.solve_potentials(c[:, -1], current, stage)

        def record(t: float, state: np.ndarray, potential: ElectrochemicalSolution) -> None:
            rows.append({
                "time_h": t / 3600, "stage": stage,
                "voltage_v": potential.cathode_voltage_v,
                "cell_soc": self._state_of_charge(state),
                "current_a": current, "c_denominator": c_rate_denominator,
            })

        while True:
            record(time_s, c, sol)
            margin = self._cutoff_margin(stage, sol.cathode_voltage_v, self._state_of_charge(c))
            if margin <= 0 or time_s >= max_t:
                break
            step_s = min(dt_s, max_t - time_s)
            c_next = self._diffusion_step(c, sol.reaction_current_a_m2, step_s)
            next_sol = self.solve_potentials(c_next[:, -1], current, stage)
            if self._cutoff_margin(
                stage, next_sol.cathode_voltage_v, self._state_of_charge(c_next)
            ) <= 0:
                cutoff_dt, c, sol = self._refine_terminal_step(
                    c, sol, current, stage, step_s
                )
                time_s += cutoff_dt
                record(time_s, c, sol)
                break
            c, sol = c_next, next_sol
            time_s += step_s
        return pd.DataFrame(rows), c

    def simulate_cycle(self, c_rate_denominator: int = 20, dt_s: float = 300.0) -> pd.DataFrame:
        charge, c = self.simulate_stage("charge", c_rate_denominator=c_rate_denominator, dt_s=dt_s)
        discharge, _ = self.simulate_stage("discharge", c0=c, c_rate_denominator=c_rate_denominator, dt_s=dt_s)
        discharge = discharge.copy()
        discharge["time_h"] += charge["time_h"].iloc[-1]
        return pd.concat([charge,discharge],ignore_index=True)
