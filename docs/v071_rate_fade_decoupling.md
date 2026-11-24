# v0.7.1 — rate capability and capacity fade

## Scope and provenance
Analysis of the two authorized collaborator CSVs, not a new physical solver or an independent cell validation.
- Charge_50cycle_new.csv SHA-256: 67080bfe917c146da08565f9385551450ab3f4455a53edc8193a9cb4f1b2c874
- Discharge_50cycle_new.csv SHA-256: 0caff987505a648200b1551cd99438452b4dcf2b40efd07b73977a20b226ac4b
- Dessantis et al. (2024), CEJA 18, 100610, [DOI](https://doi.org/10.1016/j.ceja.2024.100610), Sec. 4.1.2, Fig. 3b and Table 1. Three cycles C/30, five each C/20, C/10, C/5, two C/2, then 30 C/20 at 50 °C. All 22 published retention anchors match the CSVs to 0.005 percentage points; retention normalized to cycle 2 agrees with capacity within 0.012 percentage points. Supports inferred protocol alignment; original measurement provenance still needs confirmation.
- Each CSV contains 50 ordered positive capacity values. Wch/Wdch are not used as predictors (outcome leakage). No raw collaborator curves or full cycle arrays redistributed. The result CSVs contain rounded aggregate diagnostics; exact calculations are reproducible using the original files.

## Recovery and conditional rate penalty
Cycle 8 is the last pre-high-rate C20 point; cycle 20 is the last C2 point; cycles 21/22 return to C20. The recovered fraction is (Q_return - Q20)/(Q8 - Q20). By cycle 22, charge recovers 91.58% and discharge 93.43% of the observed drop. Charge recovery at cycle 21 is only 51.85%, whereas discharge recovers 95.52%. This is a transition effect, not evidence of a specific microscopic mechanism.

At cycle 22 the remaining same-rate gap versus cycle 8 is 7.11/5.81 mAh/g (charge/discharge). The subsequent measured decrease to cycle 50 is 27.57/24.32 mAh/g (20.79%/17.65%). Do not interpret the same-rate gap as pure irreversible loss: relaxation, starting state and history can contribute.

Conditional retrospective counterfactual: assume the unobserved C20 baseline during cycles 9–20 lies between measured cycles 8 and 22. The range of mean rate-associated shortfalls is then the anchor min/max minus each block's observed mean. Linear interpolation between anchors is an illustrative point estimate, not a fitted causal model or a prediction. These bounds are conditional on the stated assumption, not statistical confidence intervals.

| Rate | Charge conditional shortfall (mAh/g) | Discharge conditional shortfall (mAh/g) |
|---|---:|---:|
| C/10 | 8.97–16.08 | 13.53–19.34 |
| C/5 | 33.25–40.36 | 39.09–44.90 |
| C/2 | 71.04–78.15 | 83.59–89.40 |

See [block metrics](results/v071_blocks.csv), [recovery](results/v071_recovery.csv), [conditional loss](results/v071_conditional_loss.csv).

## Chronological backtest at C20
Train on cycles 22–35, freeze model coefficients, evaluate on 36–50. Constant, linear and exponential (log-linear OLS) capacity models. Repeat including transition cycle 21 as a sensitivity check. No W inputs. No per-rate fitting. These are descriptive single-cell backtests; all evaluation data have already been seen for research and compared among candidates, not a blinded independent test. No forecast beyond the measured range.

| Model | Charge test RMSE (mAh/g) | Discharge test RMSE (mAh/g) |
|---|---:|---:|
| Constant | 14.693 | 13.118 |
| Linear | 0.886 | 4.746 |
| Exponential | 1.615 | 3.598 |

Linear slope trained on 22–35: -0.93255/-1.15013 mAh/g/cycle. Charge linear predicts 105.719 at cycle 50 (actual 105.06); discharge exponential predicts 107.014 (actual 113.45). Including cycle 21 increases charge linear test RMSE to 11.604; discharge exponential to 3.869. The start choice matters. Exponential vs linear performance differs by stage; no universal degradation law is selected. See [all backtest cases](results/v071_fade_backtest.csv).

## Reproduce
```bash
python -m solid_pinn.cycle_diagnostic /private/input_dir --outdir outputs/v071
python -m pytest -q tests/test_cycle_diagnostic.py
```
Local numerical analysis executed; three synthetic regression tests passed in a standalone local copy (repository import path adapted). Repository CI is a separate check. No new coupled FEM or PINN calibration performed.

## Decision
A rate-associated recoverable component is substantial, and a history-associated component persists during repeated C20 operation. Rate and age are confounded in this single increasing-rate sequence; causal separation is not identifiable. v0.7.2 should first test D(theta)/particle radius sensitivity under frozen C20 conditions, record event capacity and voltage at C10/C5/C2, and compare both simulation and reference gaps. Establish actual initial states, rest periods, pressure, repeated randomized rate blocks and independent material measurements before selecting a coupled loss law. Preserve the original COMSOL-transfer solver and do not use cycle-specific measured capacity windows to predict those capacities. Issue #2 remains open.
