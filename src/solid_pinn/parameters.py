"""Parameters separated by provenance. All quantities are SI unless stated.

'paper' values are transcribed from Dessantis et al. (2024) Table 2 or text.
'assumption' values are not reported in the source and MUST be calibrated.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Parameters:
    # Paper: Table 2 (50 C cell).
    area_m2: float = 2.83e-5
    separator_m: float = 725e-6
    cathode_m: float = 40e-6
    particle_radius_m: float = 10e-6
    kappa_sse_s_m: float = 0.43
    sigma_cathode_s_m: float = 0.171
    sigma_aluminium_s_m: float = 3.77e7
    particle_diffusivity_m2_s: float = 2e-13
    max_solid_concentration_mol_m3: float = 47664.0
    alpha: float = 0.5
    temperature_k: float = 323.15
    faraday_c_mol: float = 96487.0
    gas_constant_j_mol_k: float = 8.314
    # Paper: experimental protocol, not Table 2.
    theoretical_capacity_mah_g: float = 165.0
    nmc_loading_mg_cm2: float = 5.0  # text says "around" 5 mg/cm2
    lower_cutoff_v: float = 2.7
    upper_cutoff_v: float = 4.2
    # Explicit assumptions / inferred parameters, NOT calibrated from the paper.
    # By default, the model derives its effective active volume fraction from
    # quoted loading and capacity, which differs from Table 2's "porosity" 0.131.
    cathode_ionic_phase_fraction: float = 0.282  # ASSUMED volume ~= mass fraction; approximate
    cathode_bruggeman_exponent: float = 1.5
    exchange_current_cathode_a_m2: float = 0.03  # ASSUMPTION, not in Table 2
    exchange_current_lithium_a_m2: float = 20.0  # ASSUMPTION, not in Table 2
    initial_soc: float = 0.02  # ASSUMPTION; paper reports cs_ini = cs_max

    @property
    def nmc_mass_g(self) -> float:
        return self.nmc_loading_mg_cm2 * 1e-3 * self.area_m2 * 1e4

    @property
    def nominal_capacity_ah(self) -> float:
        return self.theoretical_capacity_mah_g * self.nmc_mass_g / 1000.0

    @property
    def active_volume_fraction_inferred(self) -> float:
        return self.nominal_capacity_ah * 3600.0 / (
            self.faraday_c_mol
            * self.cathode_m
            * self.area_m2
            * self.max_solid_concentration_mol_m3
        )

    @property
    def active_surface_area_m_inv(self) -> float:
        return 3 * self.active_volume_fraction_inferred / self.particle_radius_m

    @property
    def kappa_cathode_effective(self) -> float:
        return self.kappa_sse_s_m * self.cathode_ionic_phase_fraction ** self.cathode_bruggeman_exponent

    def current_a(self, c_rate_denominator: int) -> float:
        if c_rate_denominator <= 0:
            raise ValueError("C-rate denominator must be positive")
        return self.nominal_capacity_ah / c_rate_denominator
