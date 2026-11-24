# v0.7.3 Gate B — reference timing and initial occupancy audit

**Decision: model-selection gate not passed.** All five original input files are now available in this execution and SHA-256 matches the historical audit. Local CPU execution of six C20 stages used the original references and digitized OCV. No parameter fitting, no holdout optimization, no Model C. No raw inputs or individual traces committed.

## Data and segmentation
Reference CSV columns are Time[h] and Voltage (V vs. Li/Li+). No current, cycle ID, capacity, or independent initial-state record. All times are nondecreasing. Counts 129/123/111 for C20/C10/C5, with 0/5/1 duplicate timestamps (extra rows beyond unique time). Max observed voltages 4.1976/4.1962/4.1974 V. Last sampled voltages 2.7000/2.6951/2.6961 V; these are observed endpoints, not event-interpolated exact cutoffs. Use the existing max-voltage split and duplicate-time average within each stage; reference capacity is derived as 165/rate * duration, not integrated measured current.

Conditional uncertainty: if reversal occurred between the highest observed voltage and the next observation, the true switch can shift by at most 0.0360/0.0026/0.0069 h, respectively. At fixed current normalization and no rest, discharge minus charge remains positive even at the latest possible reversal: C20 4.5045–5.0985, C10 0.3960–0.4818, C5 1.3431–1.7985 mAh/g. This is conditional, not proof of actual switch time. Exact equality cannot be forced by changing the split within those intervals. No inference that the source is erroneous.

If a cycle is paired, current magnitudes/normalization equal, terminal occupancy <=1 and no other lithium inventory source, then theta_initial <= 1 - (Q_dis-Q_ch)/Q_lattice. At mass-closure inventory 276.5131 mAh/g, C20 gives upper bound 0.98371 using the minimum conditional excess (0.98156 at the peak split). The collaborator model's previously documented initial occupancy 0.9818 is physically consistent with the conditional interval; not an independent measurement. It is a hypothesis for a fixed diagnostic, not a fitted value.

## Executed C20 comparison
8x20 mesh, original D and radius, unchanged phase correction and historical kinetics. Three cases: historical (eps=0.16144967, full nominal mapping, theta_initial=1), mass-consistent nominal mapping (eps=0.27056336, window 0.59671669, theta_initial=1), same mass-consistent mapping with collaborator initial occupancy 0.9818. The SOC map remains anchored at theta=1, not re-normalized to the altered starting state. Discharge inherits the charge state. No new fitted parameter. Compare voltage RMSE using historical common stage-local time convention, excluding first 60 s, no extrapolation; coverage is end-time ratio. All six stages completed at voltage cutoff and terminal occupancies within tolerance.

| Case | Charge capacity error % | Discharge capacity error % | Charge RMSE mV | Discharge RMSE mV |
|---|---:|---:|---:|---:|
| historical | +6.3963 | +2.3863 | 37.0891 | 102.1356 |
| mass_nominal | +9.0923 | +5.0839 | 36.2693 | 106.1138 |
| mass_nominal_collaborator_initial | +5.5855 | +5.0839 | 44.6031 | 106.1138 |

All six end-time coverage ratios 100%; max end-state mass residual 2.803e-9 mAh/g. The alternative initial state decreases predicted charge capacity by 5.03254 mAh/g and leaves discharge essentially unchanged; it fixes the direction of the charge/discharge imbalance (predicted excess 4.63793 mAh/g versus conditional observed 4.5045–5.0985), but worsens charge voltage RMSE relative to the mass_nominal case. Only one of six stages passes the existing absolute 3.5% capacity gate (historical discharge). No candidate passes both stages. Matching excess does not establish correct absolute occupancy or OCV mapping.

## Evidence and test status
[Timing audit](results/v073_reference_audit.csv), [C20 metrics](results/v073_reference_c20_metrics.csv), [manifest](results/v073_reference_manifest.json). The executed driver/test blob hashes match the repository copies. Local pytest run: 13 passed across convergence, inventory and reference audit tests (3 new: reversal interval, hash guard, duplicate/backward timestamps). Full GitHub CI not yet verified. No new C10/C5 solver runs, no full-trajectory occupancy proof or changed-model convergence.

## Next decision
Proceed to a *conditional* C20 calibration protocol only after recording the chosen model class, independent evidence or clearly labeled exploratory bounds for phase-specific conductivities, kinetics and OCV-to-occupancy mapping. Require both charge/discharge capacity gates, common-time voltage errors, coverage, physical bounds and convergence. Do not fit separate C-rates or separate usable windows to each observed capacity. The available two-column traces cannot independently identify initial state, phase fractions, current normalization, exchange current density and OCV mapping. Request current/time log, cycle ID, actual loading and measured or original-author occupancy/OCV map. No final model freeze, OFAT, or Model C yet. Historical kinetics remains diagnostic only.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python scripts/run_v073_reference_audit.py /private/input_dir /private/input_dir/SOLiD-PINN-OCV-Figure4 --outdir /private/v073_reference
```
