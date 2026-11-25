# v0.8.5 — Colab reproduction audit

User-returned [synthetic metrics JSON](v085_summary.json), archived byte-exact and read back from GitHub.
SHA-256: c902fca35ffd7af407b1bff62913914ae1461d28e0db8cc4e42de7b23ba72fab
Git blob: 1a6d3c1f1edaa8a77ab3894d2530d3ba6bb67f5f
Pinned source revision: 4ea0868db0c3d96a49384e9f58c2a86a923015d8.
Solver and test Git blobs match reviewed originals: 983a906fadbd94f4ec95b0251f302379f4a4cbde and 4671fd82284614a6cbcd7c6a31ffc0c2286d2876. Reported source SHA-256 matches previous benchmark manifest. All 24 expected unique method/noise/seed combinations present; finite scalar numerical metrics, 4 targeted tests reported passed, reference RK4 state RMSE 2.5224065002869637e-9. Test stdout not supplied; not independently rerun in this audit.

Original environment Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, torch 2.10.0+cpu. Colab reports Python 3.13.18, NumPy 2.3.5, SciPy 1.17.0, torch 2.14.1+cpu. Maximum absolute numerical baseline voltage RMSE difference vs rounded original CSV 9.6440738e-8 mV. Hybrid per-fit maximum interpolation/extrapolation RMSE differences 0.10134885 / 0.42933468 mV. Environment differences are plausible contributors but causation not isolated. Not bitwise reproducible neural training.

## Mean of two seeds, voltage RMSE (mV)
| Noise (mV) | Method | Original interpolation | Colab interpolation | Original extrapolation | Colab extrapolation |
|---:|---|---:|---:|---:|---:|
| 0 | misspecified | 6.07161 | 6.07161 | 12.3757 | 12.3757 |
| 0 | oracle | 8.62936e-8 | 8.62936e-8 | 4.22406e-7 | 4.22406e-7 |
| 0 | flexible | 0.398737 | 0.398737 | 1.96597 | 1.96597 |
| 0 | hybrid_pinn | 0.204278 | 0.207424 | 0.200704 | 0.365040 |
| 1 | misspecified | 6.13078 | 6.13078 | 12.2559 | 12.2559 |
| 1 | oracle | 0.109307 | 0.109307 | 0.177584 | 0.177584 |
| 1 | flexible | 0.423410 | 0.423410 | 1.73158 | 1.73158 |
| 1 | hybrid_pinn | 0.194827 | 0.249466 | 0.558664 | 0.380067 |
| 5 | misspecified | 6.37109 | 6.37109 | 11.7708 | 11.7708 |
| 5 | oracle | 0.545427 | 0.545427 | 0.852355 | 0.852355 |
| 5 | flexible | 0.637121 | 0.637121 | 0.763758 | 0.763758 |
| 5 | hybrid_pinn | 0.533324 | 0.517992 | 1.37608 | 1.37400 |

Colab hybrid improves interpolation over misspecified and simple flexible numerical baselines at each noise level, while known-physics oracle wins at 0/1 mV. At 5 mV hybrid extrapolation is worse than flexible and oracle (1.374 vs .764/.852 mV); latent RMSE .01846 vs flexible .01670. No statistical superiority claim; one synthetic truth, two seeds, known observation map, no experimental data. Future work should use multiple truths/noise draws, matched neural ODE, variable current schedules, pinned torch and deterministic settings where feasible. Do not equate interpolation across constant-current trajectories with dynamic-current prediction.

No private data uploaded; main unchanged. CI not evaluated in this audit.
