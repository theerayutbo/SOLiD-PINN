# Colab reproduction audit — v0.8.4

User-returned aggregate JSON, byte-exact GitHub archive: [v084_summary.json](v084_summary.json).
SHA256: 16003e236c517a925f46d479aa1368f3ae1255f385c9128e9ebe665507bc2269
Git blob: 0b606c0cdf189f08d94a2d991a1a19afe484ad32
Source revision: 1b4223f43aeab236a9868ed71c5bb46c21b7c028; pinned solver/test blobs verified against GitHub (71de1e9009ecbb192c3c65055aa83d1659d0c48d and 8c0cc248d0fe93451f7d0b24d476defdbd25130f).
Colab environment reported Python 3.13.18, NumPy 2.3.5, SciPy 1.17.0. 12 representative, 6 refinement, 90 repeated-noise calculations reported, all expected summary cases present, ordered finite representative quantiles. Coverage counts match prior CPU table exactly (18 entries). Comparison against rounded original CSV: maximum absolute j0 quantile delta 0.00000498249 mA/cm2; tau delta 0.000488772 h; latent voltage interval width deltas 0.000771368 and 0.168206 mV at j=1 and j=3. Maximum refinement relative delta 3.509% (previous report ~3.45%). These are close reproduction results, not bitwise numerical identity.
Only aggregate supplied; full report digest is recorded but full report absent, so individual repeats, test logs, and full report hash cannot be independently validated. No independent algorithm or experimental validation, no Bayesian PINN claim. No private data published. Next: profile likelihood / bootstrap, multiple ground truths and model discrepancy.
