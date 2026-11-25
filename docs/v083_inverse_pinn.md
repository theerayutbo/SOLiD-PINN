# v0.8.3 — Synthetic multi-current inverse PINN benchmark

## Scope
36 actual CPU fits (18 analytic nonlinear least squares, 18 inverse PINN), not experimental validation. Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, PyTorch 2.10.0+cpu. Three targeted local tests passed. Exact GitHub source/test blobs match executed copies. Full CI unverified. No private data used.

## Model and experimental design
Truth [R0,Rinf,tau,j0]=[25,12,15,0.8] (ohm cm2, ohm cm2, h, mA/cm2); illustrative, not measured LiOPA parameters. R(t)=Rinf+(R0-Rinf)exp(-t/tau); signed voltage in mV = 2jR+1000*4RT/F*asinh(j/(2j0)), T=298.15 K, symmetric alpha=0.5. Linear resistance is lumped, not a separately identified bulk and interface term. Positive bounds [1,1,2,0.1] to [60,60,80,5]. Training observations at t=0..29 h; single magnitude 1 (60 points), multi magnitudes .25,.5,1,2,4 (300 points), both polarities. Follow-up matched design cycles those five amplitudes over 30 hourly probes (60 points), both polarities. These are virtual probes at each state, not a real cycling protocol; R is time-only by construction. Independent Gaussian voltage noise std 0/1/5 mV, seeds 11/23. Common noiseless target at t=30..50 h and unseen magnitudes 1.5,3, both signs (84 observations). No experimental data or fitting to LiOPA.

LS: three fixed initial guesses, bounded analytic forward model. PINN: two 16-unit tanh hidden layers, hard initial condition R(0)=R0 and positive state via exponential, sigmoid-bounded parameters, double precision, 400 Adam steps + up to 250 LBFGS iterations. Loss = MSE(V/100 mV) + MSE(d(R/20)/dx + 50/tau*(R/20-Rinf/20)), x=t/50. 101 collocation points over full 0–50 h physics domain, no test voltage labels used. Thus prediction extends beyond observed times but within known physics domain. 201-point residual diagnostic in main runner. Fixed architecture/loss/initialization, not an optimizer hyperparameter sweep.

## Test RMSE, mean of two seeds, mV
| design | noise SD | LS | PINN |
|---|---:|---:|---:|
| single | 0 | 22.153914 | 6.231243 |
| single | 1 | 10.511188 | 6.120447 |
| single | 5 | 11.069536 | 6.030128 |
| multi | 0 | ~0 | 0.021891 |
| multi | 1 | 0.275493 | 0.275715 |
| multi | 5 | 1.313656 | 1.315729 |
| matched | 0 | ~0 | 0.001092 |
| matched | 1 | 0.299769 | 0.299012 |
| matched | 5 | 1.429171 | 1.417935 |

At 5 mV noise, matched PINN mean absolute relative parameter errors R0 1.9595%, Rinf 3.2330%, tau 19.0742%, j0 2.1317%; full multi PINN 0.6117%, 3.8129%, 9.2716%, 0.3186%. Thus accurate voltage is not proof of accurate parameter recovery. Both methods have nearly identical multi-current errors; analytical LS fits take ~0.007–0.008s and PINN ~0.65–1.68s per fit in this environment, not a rigorous speed benchmark. PINN provides no demonstrated accuracy/speed advantage on this deliberately simple, correctly specified model. Single-current LS and PINN both pick arbitrary points on a non-identifiable family: at zero noise LS training RMSE near zero yet test RMSE 22.15 mV; parameter offset tradeoff exact for fixed |j|. Singular value ratio of finite-difference log-parameter voltage Jacobian at truth single 7.71e-12, full multi 0.03415, matched 0.02961. Two seeds not sufficient for statistical inference, uncertainty intervals, or generalization across materials; matched follow-up exploratory, not preregistered. No Bayesian inference completed. No claim of global identifiability under broader model or noisy conditions.

## Reproduction
Install numpy, scipy, torch, pytest. Run from repository root:
python scripts/inverse_interface.py results.json
python scripts/matched.py matched_results.json
python -m pytest -q scripts/test_inverse_interface.py

Executed source SHA256 inverse_interface.py: 6c48a97253f7982c2f9f68ea910204fc15316fd106e2017846f89d887b06f089. Git blobs main 3f86083014bcfc82f7de0c651489ce64a374ba4d, matched 2f4f81e8550b2af96bbc9ab911f97a3baa038afa, tests e35aa33a1de5aab9a500d0d465722f5b1d420cfb. [All 36 per-fit parameter and test results](results/v083_inverse_interface.csv) rounded to 9 significant digits; full-precision generated JSON available by rerun.

## Decision
Keep analytical baseline mandatory. Advance next to uncertainty calibration (profile likelihood / synthetic repeated noise draws / Bayesian posterior with explicitly justified priors), then model mismatch and latent-state inference where analytical solution unavailable. Compare equal-budget amplitude schedules and vary truth over multiple cases. Seek independently measured multi-amplitude pulses, frequency-resolved EIS and geometry before experimental inverse inference; never treat the original fixed-current LiOPA ASR as independent evidence of kinetics. Do not merge or label full P2D/PINN experimentally validated.
