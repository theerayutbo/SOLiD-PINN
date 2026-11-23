"""v0.5 optional interface ASR + temperature scenarios; NOT a measured P2D fit."""
from dataclasses import replace
import numpy as np
from .parameters import Parameters
from .numerical import ReducedP2D, ElectrochemicalSolution


def conductivity_activation_j_mol(k25=0.16, k50=0.43, r=8.314):
    """Dessantis 2024: k25=1.6 mS/cm, k50=4.3 mS/cm."""
    if not all(np.isfinite(x) and x > 0 for x in (k25, k50, r)):
        raise ValueError("Conductivity and gas constant must be positive and finite")
    return float(r * np.log(k50 / k25) / (1 / 298.15 - 1 / 323.15))


def temperature_scenario(p: Parameters, temp_k: float, diffusion_ea_j_mol=None):
    """Arrhenius kappa anchored at 50 C, optional *assumed* diffusion Ea.

    OCV, pressure, exchange current and interface resistance are not
    temperature-adjusted, so this is NOT a temperature-calibrated cell.
    """
    if not np.isfinite(temp_k) or temp_k <= 0:
        raise ValueError("Temperature must be positive and finite")
    if diffusion_ea_j_mol is not None and (
        not np.isfinite(diffusion_ea_j_mol) or diffusion_ea_j_mol < 0
    ):
        raise ValueError("Diffusion activation energy must be nonnegative and finite")
    r = p.gas_constant_j_mol_k
    factor = 1 / temp_k - 1 / 323.15
    k = p.kappa_sse_s_m * np.exp(-conductivity_activation_j_mol(r=r) / r * factor)
    d = p.particle_diffusivity_m2_s if diffusion_ea_j_mol is None else (
        p.particle_diffusivity_m2_s * np.exp(-diffusion_ea_j_mol / r * factor)
    )
    return replace(p, temperature_k=float(temp_k), kappa_sse_s_m=float(k),
                   particle_diffusivity_m2_s=float(d))


class SeriesInterfaceReducedP2D(ReducedP2D):
    """Effective Li|LPSCl series ASR in Ohm m2; no SEI dynamics or capacitance.

    A uniform gauge shift -J*ASR applies to both phase potentials and terminal
    voltage without changing the current-conserving cathode reaction flux.
    Parent galvanostatic integration uses the new voltage for cutoff events.
    """
    def __init__(self, *args, interface_asr_ohm_m2=0.0, **kwargs):
        if not np.isfinite(interface_asr_ohm_m2) or interface_asr_ohm_m2 < 0:
            raise ValueError("interface_asr_ohm_m2 must be finite and >=0")
        self.interface_asr_ohm_m2 = float(interface_asr_ohm_m2)
        super().__init__(*args, **kwargs)

    def solve_potentials(self, surface_c, current_a, stage) -> ElectrochemicalSolution:
        s = super().solve_potentials(surface_c, current_a, stage)
        drop = current_a / self.p.area_m2 * self.interface_asr_ohm_m2
        return ElectrochemicalSolution(
            s.cathode_voltage_v - drop, s.reaction_current_a_m2,
            s.electrolyte_potential_v - drop, s.solid_potential_v - drop,
            s.solver_success,
        )
