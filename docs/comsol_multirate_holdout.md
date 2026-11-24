# COMSOL multirate transfer audit — 2026-11-24

## Scope and input provenance
The collaborator supplied wide COMSOL C/10 and C/5 global exports, reference curves, stage-dependent diffusion and resistance tables, a parameter CSV, and 50-cycle capacity tables. The original C/20 MPH/ZIP and its OCV tables were supplied earlier. No raw private curves, model archives or tables are redistributed. Independent source/licensing of the reference curves and material tables is not established; these are collaborator-supplied references, not automatically primary experimental measurements.

| Input | SHA-256 |
|---|---|
| C10_data.txt | 1024b235f42e2ec7db16e91dad9dd36ea379f0859700cd9007040bdb55a79286 |
| C5_data.txt | 3c01acb03eb907430a8324206f8a38d052c7bf974ab1d3af5e7faf122cedea32 |
| Ref_data_at_C10.csv | 04774e5dc719d75e3f7bd0d3f0447b2b564634e2979ed94451299b143336bb49 |
| Ref_data_at_C5.csv | bd127f24c6104a70c4756b654b5cf11eab2bc0d7d93708ae7cb8e098326f90ed |
| Charge_50cycle_new.csv | 67080bfe917c146da08565f9385551450ab3f4455a53edc8193a9cb4f1b2c874 |
| Discharge_50cycle_new.csv | 0caff987505a648200b1551cd99438452b4dcf2b40efd07b73977a20b226ac4b |
| Ds_lithiation_323K_RAW_for_COMSOL.csv | ab82789dc075227d1cfbb81070ea82ee3f4c16343bf6847701d71c0810b6ebf4 |
| Ds_delithiation_323K_RAW_for_COMSOL.csv | bf899de091ab24769c17040f3fe31393efbc619f081d37e46d564299943aba0a |
| R_theta_nodes_raw.csv | a87c07eff10f75ada99f6d7eb9fc6f7a5caae07863d843825281a6f928d6a5a3 |
| Used parameters.csv | 0eb47b92c8736db205b5929f3c9dc32bc10c7da323d6f26a0085727c33049a32 |

See [C20 transfer report](comsol_c20_transfer.md) for original MPH provenance. Both new exports have 45 identical global-data spatial rows, with 1055 and 522 unique time samples respectively; switch event sides preserved. COMSOL current positive for charge, opposite to this repo. Measured absolute currents 23.3475 and 46.695 microamp. Last discharge samples are not exact voltage cutoff endpoints.

| Rate | Charge time h | Observed discharge h | Charge mAh/g | Observed discharge mAh/g | Switch drop mV |
|---|---:|---:|---:|---:|---:|
| C/20 |17.371157|17.878843|143.312|147.500|48.873|
| C/10 |8.659193|8.874141|142.877|146.423|84.230|
| C/5 |4.302455|4.347545|141.981|143.469|147.578|

C20 current inferred from nominal current and model parameter table; C10/C5 read directly. Capacities use 165 mAh/g nominal; final discharge sample truncated, not exact cutoff. Reference curves split at maximum voltage and stage-local times reset there (uncertain discharge-switch alignment); repeated reference timestamps averaged within a stage; compare on common 2001-point linear time grid. Reference C10 charge/discharge durations 7.5294/7.5586 h, C5 2.9552/3.0097 h. COMSOL discharge capacity exceeds reference-derived capacity by 17.40% and 44.45% respectively. COMSOL vs reference RMSE charge/discharge: C20 30.39/10.99 mV; C10 87.38/180.49; C5 118.97/269.49. These metrics use different sampling from the FEM transfer comparison; they are not interchangeable. Cycle tables independently list 124.24/124.72 mAh/g at cycle 10 and 97.52/99.32 at cycle 15. Curve-to-cycle correspondence is plausible but not explicitly established.

## Frozen model verification
The earlier C20 saved model contains eps=0.2706, ionic fraction 0.3189, effective electronic factor 0.3159^1.5, active area 81180 m^-1, Wch=.5198, Wdch=.5380, theta_initial=.9818. CSV parameter values Wch=.5189/Wdch=.5374 differ slightly; use saved MPH for the frozen comparison. D(theta) in MPH has extra high-occupancy nodes and slight rounding differences from raw CSV. The OCV tables use percentage argument; R(theta) is included in equilibrium potential, not the disabled film resistance feature. Ref exchange current 6.5917 A/m2, alternative i0 field 100 A/m2; approximate insertion kinetics from existing TransferFEM, not a complete independent COMSOL equation audit. The full theoretical lattice inventory is 0.391319 mAh vs applied nominal 0.233475 mAh; do not conflate lattice occupancy with normalized usable SOC.

A standalone local implementation of the existing TransferFEM mathematical construction (P1 Galerkin 4 axial/10 radial elements, BDF max step 120 s, rtol 1e-7, atol 1e-9, 30 s output, exact voltage events) was executed with frozen C20 MPH parameters; only current changed. Discharge inherited charge end state. Approximate symmetric insertion j0=2*j0ref*sqrt(theta*(1-theta)), linear interpolation/constant extrapolation, variable diffusivity midpoint integration, analytical separator. Metrics evaluated on actual COMSOL sample times on common stage-local intervals, no time stretch, no extrapolation. Not a fresh COMSOL run. Results [CSV](results/comsol_multirate_fem_metrics.csv). C10 charge/discharge RMSE 0.274704/0.253139 mV, C5 0.778842/0.203832 mV; 4/4 below 1 mV. Initial sample dominates charge RMSE. No refit. Full mesh refinement and spatial validation still open.

Sensitivity: an independently executed uniform-reaction single-particle approximation (40 radial FV shells, adaptive BDF, half-shell surface reconstruction, approximate constant 100 A/m2 exchange currents and ohmic loss) compared no R, frozen C20 R and rate-specific CSV R on a 2001-point common time grid; see [SPM results](results/comsol_multirate_spm_metrics.csv). Rate-specific R gave much worse agreement with the new COMSOL exports than frozen R. Full FEM rate-specific C10 charge also worsened to 15.143 mV; remaining rate-specific FEM cases were interrupted by execution time limit and are not reported. The agreement supports but does not prove that the new COMSOL runs retained the C20 R table. Request actual C10/C5 saved studies and confirmation of any rate-specific changes. Do not optimize on these comparison outcomes and label them independent holdouts.

## Reproduction
The new importer validates repeated global rows, time/current switching, expected current magnitude and event-side preservation. The driver invokes existing TransferFEM without retuning. Its CI and exact end-to-end equivalence to the local standalone execution must be checked before calling the new code verified.
```bash
python scripts/verify_comsol_multirate.py /private/Part2_fitting_R_C20.zip /private/C10_data.txt /private/C5_data.txt
```
No raw collaborator data in GitHub. Numerical transfer success is distinct from experimental predictive accuracy; the supplied simulations fail to capture observed reference capacity loss at higher rates. Next: confirm dataset origin/cycle association, freeze model parameters, investigate a physically motivated rate/degradation dependence and validate against genuinely independent experimental data. Keep Issue #2 open.

References: Dessantis et al. (2024), DOI https://doi.org/10.1016/j.ceja.2024.100610; Fuller & Harb (2018), ISBN 9781119004257; COMSOL 6.3 documentation linked in the C20 transfer report. Collaborator data are not attributed to these sources without verified provenance.
