# v0.9.0e — Colab robustness audit

Complete first full Colab campaign, 154 cases and 924 successful fits. Original file 2,464,101 bytes, SHA256 1e78dad32288ec02d82ac27afdcd4eff9558c64d690c20a6c4511e9d027b7c88, Git blob identity 6e073dc04f67bd45b15dd93d262f0639f6c12e29. Stored in three contiguous byte-exact parts because of file size. Each part read back from GitHub and matched original byte length and Git blob hash.
```sh
cat v090e_summary.json.part01 v090e_summary.json.part02 v090e_summary.json.part03 > v090e_summary.json
sha256sum v090e_summary.json
```
|Part|Bytes|SHA256|
|---|---:|---|
|01|784607|d107258c972581a218d0b3c8bbbb8f248ec89cd4a16665d88ab18ba12ca317c0|
|02|834840|07a0d551ccacffaa1126fba3a9164d79fe6e2caa39b981a99c8dc2dd1a651dac|
|03|844654|9c4d962749692f9c28c60d55c0fb0e1cab94f899a3c17435ff3403869d1c3732|

Pinned revision 8f7e6a98d1c33ec6b347eeaa4190899fd82b17f8. Six source Git blobs match expected; reported source SHA256 metadata matches pinned notebook manifest. Python 3.13.18, NumPy 2.3.5, SciPy 1.17.0. Five tests reported passed; no independent Colab stdout. Full benchmark not independently rerun. All expected 58 calibration and 96 test keys present; 924/924 successful candidate fits; finite parameters. All raw/gated choices and both thresholds independently recomputed from saved scores. All 4000 sampled physical check dictionaries satisfy original criteria. Max mass residual 3.43170e-13, charge 3.10862e-15, resistive power identity 9.70404e-15. Bulk concentration [.14294188,.88020799], surface [.13812675,.88503256], interface state [0,.99962088]. Maximum randomized truth fit-to-reference voltage difference .493483718 mV, below 1 mV. No full energy/continuum validation.

## Mechanism choice
Each row lists gated counts in order calibrated, linear, RBF, diffusion, kinetic, series.
|Truth|IID|AR(1) rho=.8|
|---|---|---|
|null|20,1,0,0,2,1|24,0,0,0,0,0|
|rest|0,1,3,0,0,0|0,2,2,0,0,0|
|peak|0,0,4,0,0,0|0,0,4,0,0,0|
|weak_rest|0,1,3,0,0,0|0,2,2,0,0,0|
|diffusion|0,0,0,4,0,0|0,0,0,4,0,0|
|kinetic|2,0,0,0,1,1|3,0,0,0,0,1|
|series|2,0,0,0,1,1|2,0,0,0,0,2|

Thresholds .01652928193716907 (IID) and .025488729987449776 (AR1). Null raw activation 20/24 -> 4/24 (16.7%, exact two-sided 95% CI 4.74–37.38%); AR1 18/24 -> 0/24 (0%, CI 0–14.25%). Neither establishes empirical rate <=10%. Recovery-family and diffusion selection each 4/4 per stratum (exact 95% CI 39.76–100%); kinetic/series unreliable. Paired seeds across noise and alternatives, no independent pooling. Known covariance used for whitening, not estimated. Single-mechanism synthetic truth, fixed amplitudes, same reduced solver with finer mesh. Structural identifiability NOT established.

## Mean held-out results
Voltage RMSE mV, reaction density RMSE normalized. Baseline -> gated.
|Noise|Truth|Test voltage|Extra voltage|Test reaction density|
|---|---|---|---|---|
|IID|null|.370755 -> .398549|.801387 -> .839649|.000078720 -> .000089420|
|IID|rest|3.948183 -> .593463|9.257923 -> 1.133025|.000760594 -> .000119326|
|IID|peak|3.891171 -> .974413|7.639642 -> 2.038262|.000748463 -> .000192168|
|IID|weak_rest|1.250771 -> .588578|2.527065 -> .956576|.000198871 -> .000087573|
|IID|diffusion|6.761804 -> .551370|14.020718 -> 1.087739|.000662270 -> .000078489|
|IID|kinetic|.972622 -> .780111|2.097613 -> 1.649687|.000469440 -> .000352988|
|IID|series|1.269082 -> .942321|2.791215 -> 2.024203|.000416224 -> .000357589|
|AR1|null|.461478 -> .461478|.860355 -> .860355|.000085627 -> .000085627|
|AR1|rest|3.861227 -> .715742|8.199525 -> 1.656154|.000755113 -> .000129193|
|AR1|peak|3.924072 -> .883536|7.269056 -> 2.463584|.000755482 -> .000168568|
|AR1|weak_rest|1.294060 -> .635974|2.464734 -> 1.311249|.000191053 -> .000092240|
|AR1|diffusion|8.706851 -> .577625|16.344788 -> 1.412782|.000316083 -> .000074417|
|AR1|kinetic|.964471 -> .826513|2.480270 -> 2.124395|.000497014 -> .000422121|
|AR1|series|1.247926 -> .934232|3.209754 -> 2.378103|.000460657 -> .000287393|

Voltage improvement does not imply correct mechanism; especially kinetic and terminal series resistance. Next: sensitivity/Jacobian SVD and profile likelihood, joint kinetic/series parameter fit, prospective multi-timescale pulse/rest design, independently enlarged null/alternative testing, unknown covariance stress test. Keep ambiguous mechanism label rather than force selection. No real battery validation or full P2D/PINN claim.
