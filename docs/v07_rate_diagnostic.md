# v0.7 — first rate-dependent loss diagnostic

The C20-fitted COMSOL model can be transferred numerically to C10 and C5 with sub-mV agreement, but overpredicts the supplied reference capacity at higher rates. A new physics-based model has not yet been validated. This step falsifies one simple hypothesis before attempting a coupled model change.

## Hypothesis and protocol
Test an additional nonnegative terminal area-specific resistance R (ohm m2), V_new(t) = V_COMSOL(t) - J R, signed geometric current density J positive for discharge. This is a terminal-voltage surrogate, **not** a change to the coupled diffusion/reaction solution; no concentration trajectories or new cutoff capacity predictions are inferred. No changes to the frozen transfer solver. Fit one shared R on C20 only by constrained linear least squares, equal weight per stage on 1000 uniform samples each. R = max(0, sum(J*error)/sum(J^2)). Freeze and score C10/C5 without refitting. For each reference curve, split at maximum voltage, exclude pre-switch peak from discharge, reset discharge origin to peak time, average duplicate times within stage, restrict to common observed interval beginning no earlier than 60 s and first available reference sample. No time warping or extrapolation. C20 current inferred from nominal capacity; C10/C5 actual exported constant currents. Reference provenance and rate/cycle association remain unconfirmed. The C10/C5 traces have already been inspected historically; these are frozen evaluation sets, not blinded new holdouts.

## Results
Executed locally using the exact user-supplied files listed in [C20 transfer](comsol_c20_transfer.md) and [multirate audit](comsol_multirate_holdout.md). See [actual result CSV](results/v07_asr_diagnostic.csv).
The unconstrained C20 shared estimate is about -0.003606 ohm m2. A nonnegative added resistance therefore selects zero, and the baseline and frozen predictions are identical. This does not show that actual physical interface resistance is zero; the baseline already contains fitted R(theta).

| Rate | Charge RMSE mV | Discharge RMSE mV | Implied charge R (ohm m2) | Implied discharge R (ohm m2) |
|---|---:|---:|---:|---:|
| C20 |31.997|10.983|-0.005009|-0.002202|
| C10 |86.611|181.132|0.059783|0.146503|
| C5 |118.902|270.480|0.060253|0.131517|

The last two columns are diagnostic unconstrained stage-local estimates using the target residuals, NOT model parameters adopted or frozen predictions. Stage asymmetry suggests that a single extra ASR does not explain the discrepancy. It cannot establish a unique microscopic loss mechanism. Capacity evaluation requires re-solving coupled dynamics with voltage events, not post-processing.

## Cycle-dependent windows and leakage audit
The supplied 50-cycle tables contain capacity and Wch/Wdch. Direct calculation across all 50 rows gives mean capacity/window ratios of 276.512 (charge) and 276.517 (discharge) mAh/g, with ranges 276.447–276.581 and 276.482–276.580 respectively. Hence the supplied windows are numerically equivalent to measured capacity scaled by a near-constant inventory. Treat them as outcome-derived variables, not independent inputs for a prospective prediction. The cycle protocol and exact correspondence between the reference files and the 50-cycle data are not independently verified. Cycle index and C-rate may be confounded; capacity recovery during the sequence is not evidence of simple monotonic degradation. Raw tables not redistributed.

## Next controlled experiments
1. Confirm actual rate/cycle protocol and independent material/OCV/kinetics provenance. Record initial state and pressure/temperature where available.
2. Add opt-in coupled, positive additional polarization or transport law with parameters determined from independent multi-current/impedance measurements; C20 alone does not identify a rate exponent. Use matched physical-time curves, true voltage events, mass/current conservation, and mesh convergence.
3. Separate rate capability from degradation using same-rate repetitions or return-to-baseline tests; do not feed capacity-derived Wch/Wdch into held-out predictions.
4. Compare against fresh independent conditions. Preserve failed cases. Do not replace the verified COMSOL transfer model with an unvalidated empirical correction.

Reproduce with private authorized inputs: `python -m solid_pinn.rate_diagnostic /private/input_dir`. See [research atlas](research_atlas/README.md). No new experimental calibration or full v0.7 coupled solver claim. Issue #2 stays open.
