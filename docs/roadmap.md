# Execution roadmap (issues to create when GitHub repository exists)

## Milestone 0 — reproducible scaffold (implemented)
- [x] Extract reported paper parameters and explicitly tag assumptions.
- [x] Build independent reduced P2D finite-volume solver.
- [x] Verify particle mass and cathode current conservation in unit tests.
- [x] Run three galvanostatic rates on *illustrative* OCV curves.
- [x] Build synthetic physics-informed inverse of electrolyte conductivity.
- [x] Add CSV exports, diagnostic plots, tests and CI configuration.

## Milestone 1 — measurement-grade numerical baseline
- [ ] Acquire author-supplied OCV and charge/discharge traces or carefully digitise.
- [ ] Clarify paper's Table 2 epsilon=0.131 (volume fraction versus porosity).
- [ ] Clarify cs_ini and stoichiometric window; j0, lithium exchange currents,
      effective phase conductivities and cathode/SSE contact resistance.
- [ ] Add a cross-check using PyBaMM custom half-cell models (not standard DFN
      liquid-electrolyte equations) and mesh/time convergence tests.
- [ ] Calibrate ONLY at C/20; freeze parameter set and independently test C/10, C/5.
- [ ] Compare voltage RMSE, capacity errors and runtime against Fig. 5/Table 3.

## Milestone 2 — PINN beyond synthetic electrolyte inverse
- [ ] Joint inversion of conductivity and interface parameters using experimental
      voltage-time traces, with identifiability / uncertainty analyses.
- [ ] Coupled PINN for spherical Fick PDE, Butler-Volmer and axial potentials.
- [ ] Physics loss scaling, gradient balancing and stiff regime diagnostics.
- [ ] Proper held-out C-rate test and computational cost benchmark.

## Milestone 3 — publishable study
- [ ] Ablation: numerical only, PINN only, hybrid parameter estimation.
- [ ] Multi-seed training and uncertainty statistics; independent validation.
- [ ] Fully documented computation, CSV/figure provenance and reproducibility.

## Scope notes
- Never imply this version replicates published <3.5% errors.
- No redistribution of the source PDF, its figures or experimental measurements
  without checking permission/provenance.
