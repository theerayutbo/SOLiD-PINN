# Reproduction protocol and evidence gates

## Target paper
D. Dessantis et al. (2024), *Investigating sulfide-based all solid-state cells performance through P2D modelling*, Chemical Engineering Journal Advances 18, 100610. https://doi.org/10.1016/j.ceja.2024.100610

## Source-based model commitments
- Li-metal negative electrode as a boundary (Sect. 2.3, Eq. 11-13).
- Argyrodite Li6PS5Cl single-ion electrolyte, ionic Ohm's law only, Eq. 10.
- NMC622 composite positive electrode with spherical particles, Fick's law, Eq. 6-7.
- Butler-Volmer reactions, Eq. 4; Bruggeman effective transport, Eq. 5.
- Galvanostatic 2.7-4.2 V, 50 C; calibration at C/20, independent verification at C/10 and C/5 (Sect. 4.2).
- Figure 5 voltage-time curves and Table 3 signed capacity errors are acceptance references.

## Parameter audit
| Parameter | Value | Provenance / caveat |
|--|--|--|
| A | 2.83e-5 m2 | Paper Table 2 |
| L_SSE | 725 um | Paper Table 2 |
| L_cathode | 40 um | Paper Table 2 |
| r_particle | 10 um | Paper Table 2 |
| kappa_SSE | 0.43 S/m | Paper Table 2, 50 C |
| sigma_cathode | 0.171 S/m | Paper Table 2 |
| sigma_Al | 3.77e7 S/m | Paper Table 2 |
| D_s | 2e-13 m2/s | Paper Table 2 |
| c_s,max | 47,664 mol/m3 | Paper Table 2 |
| alpha_a, alpha_c | 0.5 | Paper Table 2 |
| T | 323.15 K | Paper Table 2 |
| Faraday | 96,487 C/mol | Paper Table 2 |
| molar gas constant | 8.314 J/(mol K) | Paper Table 2 |
| +/- cutoff | 2.7 and 4.2 V | Paper Sect. 2.3 |
| theoretical NMC capacity | 165 mAh/g | Paper Sect. 3.2 |
| NMC loading | about 5 mg/cm2 | Paper Sect. 3.1 |
| epsilon=0.131 | ambiguous: table calls "porosity" but equation names active fraction | **Not inserted uncritically as active fraction** |
| c_s,ini=c_s,max | Table 2 states same value; initial SoC convention not explicit | **Prototype assumes initial cell SoC 0.02** |
| kappa_cathode_effective | derived from mass-ratio-as-volume approximation (0.282)^1.5 | **ASSUMPTION** |
| j0 positive and Li | not fully specified in paper | **ASSUMPTION** |
| OCV curves | Figure 4 only, not tabular | **ILLUSTRATIVE placeholder only** |

## Numerical model status (v0.1)
The included prototype is an independent finite-volume implementation: cathode axial
charge conservation + radius-dependent diffusion, matched to a simplified Li-metal
boundary condition. Its mesh and nonlinear solver are tested for mass/current balance.
It is NOT yet a faithful COMSOL/PyBaMM calibration and is NOT paper-validated.
The PINN implements only the solid electrolyte's Ohmic equation and synthetic
conductivity inversion; extending PINN to the full coupled P2D is future work.

## Scientific acceptance gates
1. Obtain or digitise Figure 4 both OCV branches; maintain provenance and uncertainty.
2. Obtain experimental charge/discharge raw points and exact rate protocol.
3. Reconcile phase-volume fractions, concentration/SoC conventions and missing BV kinetics.
4. Cross-validate the reduced P2D with PyBaMM custom half-cell or an independent FEM solver.
5. Perform mesh and time-step convergence checks for both potential and capacity.
6. Fit one shared physical parameter set only at C/20; freeze it afterwards.
7. Predict C/10, C/5 without refitting and compare capacities and voltage curves.
8. Assess physics-residual loss, parameter recovery, uncertainty and runtime for PINN.
9. Do NOT report the article's <3.5% capacity errors as reproduced until gate 7 passes.

## Table 3 in article (signed percent errors, model minus measurement)
| C-rate | charge | discharge |
|--|--:|--:|
| C/20 | +0.6 | -2.5 |
| C/10 | -2.4 | -3.1 |
| C/5 | -0.5 | -2.6 |
