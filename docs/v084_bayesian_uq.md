# v0.8.4 — Bayesian uncertainty reference

## Executed scope
108 actual CPU posterior calculations: 12 representative design/noise/prior combinations, 6 finer-grid checks, and 90 repeated-noise fits (30 per design). Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0. Three local tests passed. Git blob hashes match locally executed files: 71de1e9009ecbb192c3c65055aa83d1659d0c48d (script), 8c0cc248d0fe93451f7d0b24d476defdbd25130f (tests). Full CI not checked. Full local generated JSON SHA256 9f9da1de46aac36059a3ecc46e75de1e858ce260d87b4e24e0a5dad4bc662d35; rounded aggregate summaries committed, not the full JSON. No private data, no neural training, no Bayesian PINN or experimental claims.

## Model and protocol
Same analytic v0.8.3 truth, bounds, observation grids and voltage relation, at 298.15 K. R0=25, Rinf=12 ohm cm2; tau=15 h; j0=.8 mA/cm2. Three designs: single current magnitude 1, 60 observations; matched schedule .25,.5,1,2,4 repeated over 30 hours with both signs, 60 observations; full multi 300 observations. Virtual probes, not a physical cycling protocol. Representative noise seed 11, Gaussian independent known sigma 1 or 5 mV. Uniform independent priors over inherited synthetic bounds [1,1,2,.1] to [60,60,80,5]; sensitivity uses density proportional to 1/j0 on same j0 bounds only. These are illustrative proper priors, not evidence-based material priors.

Marginalize R0/Rinf analytically with the Gaussian likelihood conditional on tau,j0, then sample weighted grid over tau,j0 and conditional bivariate Gaussian; reject R0/Rinf outside bounds. Global 151-point axes plus locally refined axes around bounded multistart LS (pseudoinverse curvature scale); full global support retained on both axes. Nonuniform trapezoidal weights; uniform in actual parameters, not in log grid coordinate. Six uniform-prior cases rerun with 301 base points and 32k accepted draws versus 16k; max absolute quantile change divided by fine-grid 95% width 3.45% across parameters/cases (grid and Monte Carlo effects combined). This is a numerical diagnostic, not a proof of exact quadrature. Minimum rejection acceptance for representative cases ~49%; repeated uniform cases >=71%. No MCMC used, so no Rhat or MCMC ESS claims. Pointwise equal-tail 95% credible intervals, not frequentist confidence intervals or simultaneous bands. Latent voltage intervals at t=40 h, j=1 and 3 mA/cm2, exclude future measurement noise.

## Findings
At sigma 1 mV, seed 11, uniform prior:
| Parameter | Single | Matched | Full multi |
|---|---|---|---|
| R0 | 19.782–49.940 | 24.467–25.225 | 24.859–25.108 |
| Rinf | 6.951–37.250 | 11.376–12.479 | 11.882–12.312 |
| tau | 12.815–18.120 | 14.141–17.313 | 14.267–15.302 |
| j0 | .67117–4.87128 | .79382–.81534 | .79502–.80448 |

Matched design reduces j0 interval width ~99.5% vs single at equal count. Single j0 posterior median changes 2.74449 to 1.67209 under log-uniform j0 prior; matched .80458 for both (rounded). Single current cannot identify resistance offset vs BV, even with bounded prior. At t=40, unseen current j=3, 95% latent voltage widths 55.183/2.996/1.328 mV for single/matched/full, compared with 2.100/1.185/.529 mV at j=1. At sigma 5, matched tau interval 12.486–50.619 h, despite j0 interval .77447–.88356. Longer experiment/optimized design may help; no result yet.

## Fixed-truth coverage diagnostic
30 independent noise seeds 100–129 per design, 5 mV known sigma, uniform prior. Counts in [R0,Rinf,tau,j0] order: single [19,30,22,18], matched [27,27,29,27], full [29,28,29,29]. Latent voltage coverage at j=1,3: single [23,30], matched [27,27], full [30,29]. Wide single-current intervals may cover despite weak identification; single j0 only 18/30. These are finite-repeat fixed-truth coverage results, not simulation-based calibration from prior draws. 30 repetitions and one truth are insufficient for establishing nominal calibration, and priors can affect fixed-truth coverage. No claim of statistical superiority based on these small samples. LS used for grid localization only; no frequentist interval baseline compared in this run. No Bayesian neural uncertainty comparison yet.

## Next
Add profile likelihood/parametric bootstrap and broader ground truths; compare interval sharpness and coverage under model mismatch, then compare numerical and PINN surrogate inference on non-analytic dynamics. Keep priors explicitly justified, use designed multi-amplitude current and longer observation windows; no direct LiOPA/Dessantis parameter transfer. No experimental validation, full P2D integration or Bayesian PINN claim.

[Representative summaries](results/v084_bayesian_intervals.csv), [coverage counts](results/v084_coverage.csv).
Replay: OPENBLAS_NUM_THREADS=1 python scripts/bayes_interface.py --out /private/v084.json
Tests: python -m pytest -q scripts/test_bayes_interface.py
