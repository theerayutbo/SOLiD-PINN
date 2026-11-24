# v0.7 — frozen COMSOL-informed predictions (partial)

## Executed result and provenance

The C/20 collaborator transfer in PR #9 (merge b49c286) is already merged; its Tests and PyBaMM reference workflows succeeded. This extension uses the same saved C/20-fitted model archive SHA-256 5da5d5717cea7ef70b159fda1f644708dc7fef6ad304fa61689717a6edb8cb2f. All six input tables, kinetics approximations, occupancy windows, effective conductivities and phase fractions remain frozen. No new fitted parameter. No raw collaborator assets redistributed. The local executed FEM source blob matches the merged comsol_transfer.py blob a16ef97e2218b5b2cd1598a30df23b0edf1359b9. The corrected conductivity is taken from the model file, not refitted.

At each rate, start from theta=.9818, run charge to 4.2 V, then pass the final particle profile to discharge until 2.7 V. Each C-rate resets independently; not the original experimental multi-cycle aging history. Both FEM and FVM use adaptive BDF maximum step 120 s, 30 s output plus event endpoint, nx=4,nr=10. FVM independently discretises the axial charge conservation and radial diffusion, with outer shell average used as surface concentration; shared stage driver and approximate material laws. Pair RMSE evaluated over 2001 common-time points per stage without extrapolation.

| Rate/stage | FEM duration h | FVM duration h | FEM capacity mAh/g | FVM/FEM voltage RMSE mV |
|---|---:|---:|---:|---:|
| C/10 charge | 8.658552 | 8.665662 | 142.8661 | .964136 |
| C/10 discharge | 8.879422 | 8.889053 | 146.5105 | 3.589416 |
| C/5 charge | 4.302218 | 4.309381 | 141.9732 | 1.742171 |
| C/5 discharge | 4.367949 | 4.377627 | 144.1423 | 6.283705 |

Capacity difference <0.5%: 4/4. Voltage RMSE <1 mV: 1/4. Do not claim numerical equivalence. FEM integrated occupancy balance relative to full active lithium inventory <8e-13% in these four stages; final integrated current residual <1.4e-14%. Two synthetic FVM charge/discharge current and mass balance tests and two existing transfer tests passed locally (4 tests). These synthetic checks are not field validation. Fine FEM nx6/nr16/max step60s run completed only C/10 charge (8.658496 h, 142.865187 mAh/g); remaining fine stages interrupted by execution time limit. No full mesh convergence established. PyBaMM transfer of the concentration-dependent laws is not implemented here; old reduced-model PyBaMM tests do not validate this port.

## Rate trend: negative result

Compare specific capacity normalized separately to each source's C/20 stage. Model denominator is the earlier same-grid FEM transfer (17.37085645 h charge, 17.88873931 h discharge at C/20); paper denominator is the corresponding C/20 capacity retention in Table 1 (87.35% charge, 86.44% discharge, versus the second C/30 cycle).

| Rate | Model charge % | Paper charge % | Model discharge % | Paper discharge % |
|---|---:|---:|---:|---:|
| C/20 | 100 | 100 | 100 | 100 |
| C/10 | 99.69 | 86.01 | 99.27 | 85.74 |
| C/5 | 99.07 | 69.47 | 97.67 | 68.39 |

The model overpredicts retained capacity at higher rates. The C/5 discharge gap is 29.28 percentage points. This is a descriptive comparison to different experimental cycle history, not matched experimental capacity validation. Degradation, transport/kinetic dependence, contact/interface effects and effective usable stoichiometric window may contribute; causality is untested. Do not fit the holdout rates and then call them independent predictions. The reference C/20 fitted resistance table may not transfer across rate. Obtain the original COMSOL C/10/C/5 results with identical frozen settings and full experimental protocol, then evaluate possible model discrepancy. A validated rate-dependent model needs independent calibration data or an additional held-out condition.

Rerun with authorized files:
```bash
python scripts/predict_frozen_rates.py /private/Part2_fitting_R_C20.zip --rates 10 5
```

[Executed summary CSV](results/v07_frozen_rate_summary.csv). Published source: Dessantis et al. (2024), Table 1, p.5, https://doi.org/10.1016/j.ceja.2024.100610. For transfer equations and references see [COMSOL transfer report](comsol_c20_transfer.md). This work is not a new experimental fit or a claim of original paper reproduction.
