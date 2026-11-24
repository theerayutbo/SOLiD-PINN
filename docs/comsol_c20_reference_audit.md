# COMSOL C/20 sequential voltage-reference audit (2026-11-24)

## Provenance and limits

User supplied `V_vs_t_C20_sim.txt`, header model `Part2_fitting_R_C20.mph`, COMSOL 6.3.0.290, exported Nov 24 2026 17:45. 2118 voltage/time rows; ordinary interval 60 s. Raw collaborator file is not redistributed in this repository. No original MPH, actual current, SOC, parameter table, OCV function, mesh/solver settings or equations are contained in this export. The C/20 label follows the filename/model name. Treat as an unmatched sequential simulation reference, not experimental data and not the six independent uniform-start v0.6.1 scenarios.

Observed initial voltage 2.73085450 V, peak 4.20004865 V; paired time at 17.37115676 h has pre/post switch voltages 4.20004865 and 4.15117531 V (48.87334 mV difference). Final sample 35.25 h, 2.71418916 V (not exactly 2.7 V); observed discharge duration 17.87884324 h. Both samples at switch are retained. This is a sampled trace, not evidence of the exact final cutoff. The jump may include OCV branch change and kinetics/ohmic polarization; it does not independently identify interfacial resistance.

## Executed comparisons

Local FVM numerical.py and OCV implementation matched GitHub blobs cb9d03ba and ccd9e5a9. Explicit sigma_cathode_s_m=0.17 overrides local legacy default. Mesh 6x10, time step 60 s, C/20 current from model nominal capacity 0.233475 mAh. Discharge inherits charge terminal concentration. Compare on stage-local physical time, using observed samples on overlapping intervals, with no extrapolation or time stretching. The actual COMSOL current and SoC are unknown. No new experimental calibration.

| Scenario | Charge RMSE mV | Discharge RMSE mV | Charge duration h | Discharge duration h |
|---|---:|---:|---:|---:|
| synthetic OCV, historical j0 and SoC | 60.482 | 147.703 | 17.840 | 19.280 |
| private digitized Fig.4 OCV, historical j0 and SoC | 64.266 | 100.675 | 16.976 | 18.417 |
| digitized OCV, fully lithiated start | 50.286 | 100.675 | 18.517 | 18.417 |
| digitized OCV, fully lithiated, j0=0.12 A/m2 | 54.036 | 100.282 | 19.166 | 19.066 |

Historical j0=0.0566011934 A/m2; initial SoC 0.0770454572. Charge coverage 97.727% in digitized frozen case, 100% otherwise; all discharge coverage 100%. RMSE including t=0 can be influenced by initial transient (excluded-t0 RMSE also supplied). Digitized OCV data are privately generated figure reconstructions, not original author data. Raw digitized points not committed. Results: [metrics CSV](results/comsol_c20_exploratory_metrics.csv).

Three additional probes at j0=0.25,0.5,1.0 A/m2 failed nonlinear residual checks (1.66e-5,2.33e-5,4.15e-5 respectively despite root reporting convergence). No metrics for failed runs. These are sensitivity experiments, not accepted material parameters. No selection based on this single unmatched reference. The 48.9 mV switch should be investigated using the actual COMSOL OCV curves and current; do not treat it all as ohmic loss. Changing initial SoC to zero is consistent with Table 2's c_ini=c_max but is not proven to be the COMSOL state. Relative discharge discrepancy remains about 100 mV and can reflect OCV mapping, actual current, phase fractions, kinetics or cutoff. Do not claim four-solver equivalence.

## Corrected numerical benchmark, separate protocol

CI [run 45452297260](https://github.com/theerayutbo/SOLiD-PINN/actions/runs/45452297260) at e95b63e succeeded with sigma=0.17; [actual 36-row CSV](results/v061_three_solver_matched.csv). 16/18 pairwise voltage RMSE gates below 1 mV, max PyBaMM/FEM RMSE 0.073122 mV, all 18 capacity differences below 0.5% (max 0.026108%). FVM C/5 discharge comparisons exceed target (1.032194 mV vs PyBaMM, 1.076420 mV vs FEM). Do not mix the corrected uniform-start benchmark with this sequential COMSOL export.

## Reproduce and next evidence

`python scripts/compare_comsol_c20.py /private/V_vs_t_C20_sim.txt --charge-ocv /private/ocv_charge_digitized.csv --discharge-ocv /private/ocv_discharge_digitized.csv`

For physical equivalence, request exact current, COMSOL parameters/units, geometry, initial and terminal concentration, equilibrium potential interpolation tables, BV exchange-current law, electrolyte and active phase fractions, resistance expression, cutoff events, spatial fields and C/10/C/5 data. Freeze parameter selection before evaluating higher-rate hold-outs. Keep permission-restricted files private. Source: Dessantis et al. (2024), [DOI](https://doi.org/10.1016/j.ceja.2024.100610), Table 2 and Figs 4–5; Fuller & Harb (2018), [project BibTeX](../CITATIONS.bib), Ch 3/5/7. Issue #2 remains open.
