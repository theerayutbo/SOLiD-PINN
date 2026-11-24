# v0.7.3 Gate A — C/20 numerical convergence

Executed by ChatGPT on a local CPU on 2026-11-24; not a simulated or synthetic result. The original v0.7.2 solver was retrieved at aa8a1bb95a444e339d8ecfb45db0661099d2df8f, hash-matched to the Colab manifest, then parameterized without altering default physical or solver values. Local and GitHub blob hashes of the executed solver, driver and test file match. Input OCV charge/discharge hashes match v0.7.2; no reference CSVs were needed for this solver-to-solver comparison. Colab MCP remains unavailable (403). Run identity 89814c9b558b94803d45.

## Evidence
- [12-stage metrics](results/v073_gate_a_metrics.csv), [10 pairwise comparisons](results/v073_gate_a_comparisons.csv), [manifest](results/v073_gate_a_manifest.json), [execution status](results/v073_gate_a_status.json).
- Eight new local tests passed: default controls equivalence, invalid controls, incorrect state shape, common-time comparison/gate and input hash guard. Full repository CI pending.
- Historical kinetics only, C/20 charge followed by discharge with inherited state within each run. Same OCV and physical parameters as v0.7.2. Separate mesh initializations; output sampling fixed at 30 s. No private OCV arrays, individual traces or concentration states committed.

## Result
All 12 stages reached voltage cutoff. All ten successive refinement comparisons passed the declared capacity/cutoff 0.5% and voltage RMSE 1 mV criteria on their common time. Maximum end-state mass balance residual 2.17290e-9 mAh/g. Terminal normalized state range 0.07360159–0.99724452, within bounds (not a full trajectory occupancy proof).

| Comparison | Charge RMSE (mV) | Discharge RMSE (mV) | Max capacity change (%) |
|---|---:|---:|---:|
| 4x10 -> 8x20 | 0.0126817 | 0.0485812 | 0.00135619 |
| 8x20 -> 16x40 | 0.00317006 | 0.0121543 | 0.000339286 |
| 120 -> 60 s | 0.00000207234 | 0.000000907714 | 1.98958e-9 |
| 60 -> 30 s | 0.00000114329 | 0.000000643145 | 9.96758e-10 |
| Tight tolerance | 0.000151438 | 0.000000176361 | 8.52873e-11 |

Tightest run capacities 152.6875403 and 152.1530097 mAh/g. Compared with the archived C20 duration-derived reference capacities 143.50875 and 148.60725 mAh/g, errors remain +6.39598% charge and +2.38599% discharge. The change from historical baseline is only ~0.0024/0.0026 mAh/g. Capacity and cutoff time are proportional at fixed current, so these two criteria are not independent.

## Decision
The tested C20 numerical convergence subgate passes. Mesh and time integration error are far too small to explain the C20 capacity discrepancy. This does not establish model-form validity, all-rate convergence, field convergence, or full-trajectory occupancy. A separate reference-voltage RMSE was not recomputed because the three collaborator reference CSVs are unavailable in this local session; use archived reference capacities only for this comparison. Other configurations retain their historical baseline records (PR #17), not new refinements. No new fitting, no final freeze, no OFAT, no Model C. Before Gate B, review full-trajectory physical bounds if needed and obtain independent evidence of active fraction, loading, operating window, and phase interpretation. Historical kinetics remains provisional. The 8x20 mesh is suitable for exploratory C20 diagnostic calculations within the tested criteria, but recheck convergence if parameters or C-rate change.

Reproduce with authorized OCV files:
```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python scripts/run_v073_convergence.py /path/to/SOLiD-PINN-OCV-Figure4 --outdir /private/v073
```
The driver records aggregate evidence; it does not resume interrupted stages. For a partial --count run, status is partial rather than a complete Gate A assessment. Use a single writer. Do not start OFAT before the C20 selection gate.
