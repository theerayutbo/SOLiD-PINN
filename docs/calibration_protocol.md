# v0.3 — Preliminary experiment-guided calibration

## What this does

This workflow uses the v0.2 reduced finite-volume P2D model as a baseline,
introduces *user-provided* charge/discharge pseudo-OCV curves (SOC, voltage_v),
and fits two parameters **only to C/20** (exchange current density of the cathode
and the assumed initial SOC). It then predicts C/10 and C/5 with the parameter
set unchanged. This is **NOT** calibration of all electrochemical properties,
proof of parameter identifiability, full-P2D validation, or a substitute for
experimental raw data.

The constant kappa = 0.43 S/m and solid diffusivity = 2e-13 m2/s are **not**
optimized; they remain as values reported in Dessantis et al. (2024), Table 2.
Other assumptions, such as ionic phase volume fraction and metallic-Li BV
exchange current, remain unchanged. The fitted j0 and initial SOC must **not**
be interpreted as independently measured or uniquely identified material
constants; both absorb other model errors.

## Data input

Local user-provided files only (no figure derivatives in public repository):

- `ocv_charge.csv` and `ocv_discharge.csv`: `soc,voltage_v`, with SoC 0..1
- `c20.csv`, optional `c10.csv`, `c5.csv`: `time_h,voltage_v,stage`
- `stage` is either `charge` or `discharge`. Both must appear, with at least
  three strictly increasing time samples in each stage.

Sample invocation:

```bash
pip install -e '.[dev]'
python scripts/calibrate_c20.py \
  --charge-ocv /private/ocv_charge.csv \
  --discharge-ocv /private/ocv_discharge.csv \
  --c20 /private/trace_C20.csv \
  --c10 /private/trace_C10.csv --c5 /private/trace_C5.csv \
  --nx 4 --nr 6 --dt 300 --max-nfev 25 \
  --outdir outputs/calibration
```

## Quantitative diagnostics

- Stage-wise **voltage RMSE and MAE**, in V, over overlapping time support.
- `coverage_fraction` reveals if a predicted curve ends before measurements.
- Stage duration mismatch in hours; a duration penalty is included in fitting
  so very short simulations cannot trivially reduce voltage error.
- Stage time is measured relative to the **first available point** of each stage
  for both simulation and observation. For digitised curves that omit near-vertical
  endpoints, this introduces a potential **time-registration bias**; duration
  mismatch values should be considered approximate.
- User may evaluate held-out C/10 and C/5 but must **not** use them to choose
  or adjust fitted parameters before independent validation.

## Current example / scientific constraints

Dessantis Fig. 4 supplies approximate pseudo-OCV (C/30, 50 C); Fig. 5
contains red *experimental* curves. A private local pixel-digitisation of the
latter is possible but carries line-thickness (~several mV), time-axis, origin,
peak, and endpoint uncertainty. Digitized figures are **not** raw observations.

At 50 C, the reported Fig. 5/Table 3 errors require precise source traces,
missing interface parameters and a validated numerical model. The source paper
states data available upon request (not bundled); it is not appropriate to
publicly redistribute derived numerical arrays or source figures without
checking permissions under the paper's CC BY-NC-ND licence.

## Computational choice: local CPU vs Colab

Default coarse run (nx=4, nr=6) typically fits in seconds to minutes on a CPU,
with no GPU or Colab startup/IO benefit. Colab becomes useful for large PINN
training, ensembles/multi-seed quantification, or high-resolution parametric
surrogates; it is not required for this calibration stage.

## Next acceptance gates

1. Obtain original author C/20, C/10, C/5 traces and both pseudo-OCV branches.
2. Reconcile SOC definition, phase fractions, OCV axes and loading precisely.
3. Compare with a separately implemented PyBaMM or FEM solid-electrolyte model.
4. Quantify mesh/time-step convergence and parameter identifiability; release
   numerical uncertainties and independent hold-out fit scores.
5. Only then evaluate reproduction of reported Table 3 capacity errors.
