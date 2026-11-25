# v0.8.2 — passive symmetric-cell observation model

Actual CPU execution on user-submitted LiOPA evidence ZIP (SHA256 219d95bee956a186e4e99821e44c4b64f165bd6bc76c2c11e9d67a5c26d90ce1); 12/12 exports match supplied manifest, selected ASR sheet SHA256 6648d1faef5a26d5f0c77c41cdaf90274798081d460cffd83d5e9f6b4ac4b0fc. Source attribution: https://doi.org/10.5281/zenodo.17816356 (CC BY 4.0). Source workbook bytes absent; only export identities checked. Python 3.13.5 NumPy 2.3.5 pandas 2.2.3 SciPy 1.17.0. Executed script SHA256 e7f60541a92f78c55a4211517a256419d5619a1f805644875bb08aa0466cdf75; local/repository blob match. Four local tests passed, repository layout tested; full CI unverified. No raw data committed.

## Observation and identifiability
Signed effective observation V=2*j*R_eff(t) (mV, mA/cm2, ohm cm2). This is a lumped two-electrode model, not uniquely isolated interface resistance. At fixed |j|, the linear ohmic term and symmetric Butler-Volmer asinh term are exactly proportional, even when current polarity reverses. Bulk and linear interfacial resistances are also structurally confounded. In the actual data, |j| ranges 1–1.00016, exactly 1, and 1–1.00047 for Pristine, 2 OPA, 2 Li-OPA; all nonzero valid observations have V*j>0. Illustrative normalized design [j, asinh(j)] (reference scale 1 mA/cm2, not measured kinetic scale) has smallest/largest singular value ratio 2.13e-6, 1.13e-15, 6.94e-6. This is a conditioning diagnostic at a representative fixed scale, not a general nonlinear parameter confidence interval. Instrument-scale current variations do not provide designed multi-amplitude excitation.

## Dynamic candidate
dR/dt=-(R-R_inf)/tau; R0,R_inf>=0; 1<=tau<=1000 h. Deterministic multistart constrained least squares on hourly ASR medians, hours 1–29; compare constant mean and relaxation without refitting at hours 30–49, then later available blocks. Predictions use hour index, not sub-hour dynamics. Report signed voltage RMSE as square root of average hourly mean squared error of individual observed voltages, equal hour weight. ASR loss and voltage evaluation are algebraically related, not independent evidence. Exclude final partial hour. Previously explored traces and time windows: retrospective comparison, not untouched holdout or independent-cell validation.

| group | constant voltage RMSE mV | relaxation voltage RMSE mV |
|---|---:|---:|
| Pristine | 1.45543 | 0.78831 |
| 2 OPA | 1.22415 | 1.83673 |
| 2 Li-OPA | 1.75281 | 1.78310 |

Relaxation improves Pristine 45.84%, loses to constant in both coated groups on the common interval. Li-OPA hours 140–399: 5.31499 vs 5.34019 mV; OPA last seven bins: 10.28146 vs 9.48375 mV. No universal dynamics selected. R0 is model extrapolation to t=0 (startup excluded), tau an effective empirical time scale, not independently identified reaction constant. Retain negative outcomes.

## Next gate
1. Use effective resistance only; do not transfer symmetric-cell ASR directly to the full-cell cathode or Dessantis.
2. Independent designed currents at multiple amplitudes, known geometry and conductivity, and frequency-resolved EIS are required to separate bulk/interface/kinetics. Existing EIS export does not include frequency. 
3. Construct synthetic multi-amplitude identifiability benchmark with noise and known ground truth; compare constrained least squares with a small neural ODE/PINN using identical data, split, physics residual and passivity constraints. Require parameter recovery and uncertainty, not merely voltage RMSE. Use independent time/cell conditions before experimental generalization claims.
4. This work is analytical ODE plus fitting, not neural training, a solved P2D model or independent experimental validation.

[Metrics](results/v082_symmetric_dynamics.csv), [conditioning diagnostics](results/v082_identifiability.csv).
Replay: python scripts/symmetric_benchmark.py /private/SOLiD-PINN_open_evidence.zip --out /private/v082.json
