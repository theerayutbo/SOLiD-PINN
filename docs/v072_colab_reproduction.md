# v0.7.2 — completed Colab reproduction (24 November 2026)

## Evidence and scope
User-executed Colab CPU run, solver revision `aa8a1bb95a444e339d8ecfb45db0661099d2df8f`, notebook revision `46d10cd5c5c249bd5dc848400ecd9f84c8aab672`. Archive: [18-stage metrics](results/v072_colab_metrics.csv), [manifest](results/v072_colab_manifest.json), [aggregate discharge figure](results/v072_colab_capacity_error.svg). Historical 11-stage [metrics](results/v072_paper_reproduction_metrics.csv) remain unchanged. The figure is regenerated from aggregate CSV, not the original Colab PNG. Original inputs, predictions, checkpoints and unpublished reference traces are not redistributed.

The manifest reports five input SHA-256 values matching the v0.7.2, C20 transfer and multirate audit records; both source digests match the pinned GitHub source. Python 3.13.18, NumPy 2.2.6, SciPy 1.15.3, pandas 2.2.3. 4 axial / 10 radial elements, BDF max step 120 s, output step 30 s, rtol 1e-7, atol 1e-9. No new fitting. This is an audit of submitted aggregate evidence, not an independent solver rerun or direct inspection of concentration checkpoint states.

## Reproducibility
All 18 unique configuration/rate/stage combinations report complete and voltage cutoff; 11/11 overlap historical records, 7 newly completed stages. Maximum absolute differences over the 11 matched rows: capacity 1.09406e-8 mAh/g; voltage RMSE 1.73674e-7 mV. Maximum reported end-state mass-balance error 6.08793e-10 mAh/g. Small mass-balance residual is not a mesh convergence or experimental validation result.

## Scientific result
Signed capacity errors (%) relative to the collaborator reference duration convention:

| Configuration | C20 chg | C20 dis | C10 chg | C10 dis | C5 chg | C5 dis | Mean absolute error | Mean stage RMSE (mV) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| literal_0131 | -6.93 | -10.19 | 7.24 | 6.68 | 35.88 | 33.06 | 16.66 | 146.43 |
| inventory_derived | 14.73 | 10.73 | 32.23 | 31.57 | 67.64 | 64.24 | 36.86 | 189.16 |
| historical_kinetics | 6.40 | 2.39 | 17.95 | 16.82 | 42.67 | 38.82 | 20.84 | 106.95 |

Only 1/18 stages meets the project absolute capacity-error gate of 3.5% with voltage termination. Historical kinetics C20 discharge passes, but C20 charge fails (+6.40%). C20 charge/discharge RMSE 37.09/102.14 mV, reported end-time coverage 100%/100%. Literal C20 coverage 93.07%/89.81%; common-interval RMSE cannot be interpreted as equal full-duration coverage. Mean stage RMSE is unweighted, not pooled point-wise RMSE.

At fixed active fraction 0.16144967261842047 and phase 0.131, lowering cathode exchange current density from 6.59173895 to 0.0566011934 A/m2 improves the reported errors versus inventory_derived; this is a controlled comparison in this model, not independent evidence of physical j0. All variants overpredict high-rate capacity; the literal case has the smallest all-stage mean absolute capacity error, historical kinetics the smallest unweighted mean stage RMSE. No variant meets both C20 capacity gates. Do not call the historical kinetics variant calibrated or freeze a final baseline yet.

The comparison target is collaborator reference, not author-verified experimental raw data; time coverage is end-time ratio and initial 60 s excluded in RMSE. The original article cycle/endpoint identity remains unresolved. Numerical reproducibility is established for the archived common rows, not exact paper reproduction or independent experimental validation.

## Next gate
Historical kinetics is a **provisional diagnostic candidate** for C20 convergence work, not a selected final model. Freeze the documented candidate for convergence tests only. See [v0.7.3 work package](v073_convergence_sensitivity_plan.md). No Model C implementation or claims.
