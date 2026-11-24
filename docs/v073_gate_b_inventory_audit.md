# v0.7.3 Gate B — physical inventory and SOC audit (24 November 2026)

**Decision: NOT PASSED.** Conditional mass closure is improved, but neither candidate meets both C20 capacity gates. No final parameter freeze, calibration, OFAT or Model C.

## Source audit
Dessantis et al. (2024), DOI https://doi.org/10.1016/j.ceja.2024.100610, pp. 3–7: Eq. 3 defines active fraction, Eq. 5 uses porosity in Bruggeman scaling, Table 2 labels epsilon_s=0.131 porosity, 40 um cathode, 725 um separator, radius 10 um, cmax=cini=47664 mol/m3, D=2e-13 m2/s, conductivities 0.43/0.17 S/m (0.17 has library footnote), 323.15 K. Section 3 reports approximate active loading 5 mg/cm2, 67.4:28.2:4.4 solids mass ratio before binder, and 165 mAh/g C-rate convention. Fig. 4 uses charge SOC and discharge SOD axes; the verified local discharge digitization is already reversed to an increasing SOC coordinate. Section 4.1.3 identifies pseudo-OCV from the second C/30 cycle; not a measured absolute lattice stoichiometry map. Exact cathode/Li exchange currents and distinct phase fractions are not specified. No independent evidence for the code's constant j0 or common 0.131 conductivity correction. Fig. 5 uses C20 calibration and changes only current for C10/C5 validation. Data available upon request.

## Conditional mass closure
Assume nominal LiNi0.6Mn0.2Co0.2O2, one Li per formula unit, molar mass 96.9282876 g/mol; cmax times molar mass implies 4.61999 g/cm3; loading/(density*thickness) implies active fraction 0.27056336. Independent NMC622 measurement 4.76 g/cm3 (Batteries 2021, 7, 70, DOI https://doi.org/10.3390/batteries7040070) is a plausibility check only, not the paper's sample. At 40 um and nominal loading, 0.131 and 0.16144967 would imply 9.542 and 7.742 g/cm3 respectively. The collaborator fitted active fraction 0.2706 closely matches conditional mass closure but is not author confirmation. Full one-Li inventory 276.51313 mAh/g; nominal 165 mAh/g implies a 0.59671669 occupancy span if interpreted as accessible capacity, not a measured window. Initial occupancy=1 is from Table 2; lower nominal endpoint 0.40328331. Actual OCV-to-occupancy calibration is unresolved.

## Executed structural diagnostic (not OFAT)
Same historical j0 and provisional phase correction, constant D, radius, currents and 8x20 mesh. Compare historical inventory (eps=0.16144967, SOC=1-theta) against coupled mass-consistent inventory and nominal SOC mapping clip((1-theta)/0.59671669,0,1). This is a diagnostic hypothesis, not a calibrated physical model; clipping is an explicit assumption. Each discharge inherits its charge state. OCV hashes verified; no reference CSVs used; compare capacity only with historical duration-derived reference values. All 4 stages reached voltage cutoff, terminal states within [0,1], max end-state mass residual 2.803e-9 mAh/g. Two local tests passed (mass closure, SOC mapping); repository test path bootstrap added for CI. No full trajectory or mesh convergence for changed model.

| case | charge capacity | discharge capacity | signed charge error | signed discharge error |
|---|---:|---:|---:|---:|
| historical | 152.68802 | 152.15353 | +6.39631% | +2.38634% |
| mass consistent + nominal window | 156.55697 | 156.16236 | +9.09228% | +5.08394% |

Units mAh/g. The structural alternative worsens both capacity errors; retain as negative result. No reference voltage RMSE recomputed. [Metrics](results/v073_gate_b_inventory_metrics.csv), [manifest](results/v073_gate_b_inventory_manifest.json).

## Reference consistency constraint
Archived C20 duration-derived charge/discharge capacities 143.50875/148.60725 imply discharge/charge=1.03552745. For the modeled fully occupied initial state, inherited discharge state, fixed current normalization and no lithium-generating side reaction, discharge capacity cannot exceed preceding charge capacity. Thus exact simultaneous matching is incompatible with these assumptions if the reference represents a paired complete cycle with identical normalization. This is a diagnostic flag, not proof that the reference or paper is wrong. At the +/-3.5% project gate, ranges overlap (charge 138.486–148.532, discharge 143.406–153.809 mAh/g), so tolerance-level matching is possible. Audit timestamps, cycle identity, current normalization, initial occupancy and endpoints before fitting. Do not use observed capacities to tune separate rate-dependent stoichiometric windows.

## Next
Acquire C20 reference trace plus cycle/current metadata privately. Obtain author model material fractions, OCV mapping, electrode loading and exchange-current settings, or document missing evidence. Pre-register C20 objective using both stages, common-time voltage error, capacity/cutoff/coverage and physical bounds. No fitting until objective and bounds are supported, no final freeze until both C20 capacity gates and numerical checks pass. Keep C10/C5 for retrospective frozen evaluation. No raw arrays committed.
