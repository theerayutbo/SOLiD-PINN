# v0.8.5 — Synthetic model discrepancy and hidden-state benchmark

24 executed CPU fits, 6 hybrid PINN, 18 numerical. Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, torch 2.10.0+cpu. Four targeted tests passed. Executed source SHA256 c924545b01db9c1d6a54c4429b9c533cfe4081ea64e55a638f98ce3ca78b7555; Git source/test blobs verified against local. No experimental input. No full CI or independent replication yet.

## Protocol
Known synthetic observation map V=2j[12+13 exp(-t/15)+18x]+K asinh(j/(2*0.8)), K=1000*4RT/F in mV at T=298.15 K. State x in [0,1] starts at zero; dx/dt=a(j)(1-x)-0.06 x^3. True a=0.1*j^2/(1+0.7*j^2) per h. Reference solve_ivp with rtol 1e-11 and atol 1e-13. RK4 dt=.25h state RMSE versus reference 2.5224e-9 across eight protocols. Synthetic constants are illustrative, not measured material properties. The latent state is not directly supplied as a training label but is algebraically observable from voltage given the known map and nonzero j; this is not a proof of hidden-state identifiability in real batteries.

Four constant positive current amplitudes .25,.75,1.5,3 mA/cm2; train 0–29 h, 120 voltage points, Gaussian voltage noise SD 0,1,5 mV seeds 11,23. Evaluate noiseless truth at 30–50 h, unseen amplitudes .5,1,2 (interpolation), 4 (extrapolation relative to data). Physics collocation spans 0–50 h and .25–4 current domain, without test labels. No variable-current trajectories tested.

Numerical baselines share same state dynamics and observation map: misspecified rate p*j^2; oracle rational saturation (true functional family supplied, coefficients fitted); flexible monotonic piecewise linear rate with four positive increments and last segment linearly extended. All fit voltage with bounded least squares and RK4. PINN learns positive rate via softplus times j^2/16, state via exponential hard x(0)=0 and 0<=x<1, two networks with 12 and 24/24 tanh units, 800 Adam and up to 200 LBFGS steps. Loss normalized voltage error /50 mV squared plus squared dimensionless residual 50*(dx/dt-a*(1-x)+0.06x^3); 341 collocation points. Independent residual grid and RK4 learned-rate state gap measured. No model architecture sweep or equal-parameter-capacity matching; numerical flexible baseline is simple, not exhaustive.

## Mean of two seeds (mV)
| Noise | Model | Interpolation late | Extrapolation late |
|---|---|---:|---:|
| 0 | misspecified | 6.072 | 12.376 |
| 0 | flexible | .399 | 1.966 |
| 0 | oracle | ~0 | ~0 |
| 0 | hybrid PINN | .204 | .201 |
| 1 | misspecified | 6.131 | 12.256 |
| 1 | flexible | .423 | 1.732 |
| 1 | oracle | .109 | .178 |
| 1 | hybrid PINN | .195 | .559 |
| 5 | misspecified | 6.371 | 11.771 |
| 5 | flexible | .637 | .764 |
| 5 | oracle | .545 | .852 |
| 5 | hybrid PINN | .533 | 1.376 |

Hybrid improves interpolation vs misspecified and piecewise flexible baselines at all tested noise levels. At 5 mV its extrapolation is worse than both flexible and oracle. Oracle is an advantaged correctly specified comparator, not an available real-world model. At 5 mV hybrid latent state RMSE .01927 vs flexible .01670; voltage-only gains do not establish superior latent recovery. Learned-rate RK4 state gap averages .00196–.00281 across noise levels (dimensionless), scaled ODE residual .0141–.0161, not exactly zero. Two seeds, one truth, no statistical superiority claim; zero-noise numerical repeats identical. Numerical fits ~.06–.13 s; PINN ~1.7–2.3 s on this CPU; not rigorous performance benchmark.

Next: variable-current trajectories, independent hidden observation/geometry, stronger flexible numerical and neural ODE comparator, multiple truths and uncertainty under mismatch. Do not advance to full experimental P2D-PINN claim from this benchmark.

Replay: OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/mismatch_benchmark.py --out results.json
Tests: python -m pytest -q scripts/test_mismatch_benchmark.py
[Per-run metrics](results/v085_mismatch_metrics.csv).
