# v0.9.0a — reduced x-r electrochemical bridge

72/72 optimizer success flags, four targeted tests passed locally. Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0. Original JSON SHA256 433aaea9ded4dcf53ab114cd5ec51b84826305144a418a887e6bd68a5cf9acd0. Executed solver/test blobs bfd2dc26f1aeb3929d452227bad3034140236d61 and c865881fdd3e5049304a3ef783a6144067ba1433 match GitHub.

## Model
Standalone illustrative single-ion half-cell, not the existing full solver or validated Dessantis parameters. Axial 4 cells, radial 6 spherical shells. Normalized concentration, positive J inserts lithium; J=.025*u per hour, linear OCV 4.1-.8*c_surface. Linearized local charge transfer and axial electronic/ionic resistance network, common separator drop. Branch currents p satisfy A*p+V0*1=U and sum(p)=J. Shell-volume-weighted diffusion with flux continuity, particle source n*p, inventory change equals integral of J. Matrix exponential exact for piecewise constant input in linear semidiscrete system, compared to solve_ivp on same spatial operator. Terminal interface drop -2*J*x, x'=a(1-x)-d*x, a=.35*u^2/(1+.7*u^2), d from null/rest/peak synthetic laws. Positive fixed-center RBF or piecewise linear d with fixed smoothness penalty, fitted a and d coefficients from training voltage only; oracle knows closure shape. At fixed current terminal closure does NOT change cathode fields; not a fully coupled spatial closure. No dynamic collocation PINN, no nonlinear BV, no experimental calibration, no adaptive gate port yet.

## Verification and blocker
Maximum normalized inventory residual 6.11e-15; charge/current and algebraic residual max 1.36e-15 (combined numerical units, see implementation); sampled concentration range [.24735,.77829], closure state [0,.961263]. Same-mesh time integrator max voltage difference 1.47e-9 mV, NOT independent PDE validation.
| Profiles | 4x6 -> 8x12 max delta mV | 8x12 -> 16x24 max delta mV |
|---|---:|---:|
|train|15.5051|8.4613|
|test|10.3282|5.6393|
|extra|20.6559|11.2761|

Spatial convergence not established to 1 mV. Do not proceed to experimental fit or claim sub-mV physics fidelity. Synthetic labels and fits share coarse mesh, so discretization error cancels in comparison; model discrepancy can absorb numerical error on a different mesh. Next: surface reconstruction, boundary half-cell resistance treatment, separate axial/radial refinement, cross-grid synthetic falsification, existing nonlinear solver integration. Colab notebook repeats fits and separate axial/radial refinement, without automatically treating a failed mesh criterion as success.

## Results
Three truths, two noise SDs, three paired seeds, four models; 72 fits. Training 4 profiles x49 samples; two held-out profiles each for interpolation and mixed extrapolation. Same fixed regularization, no tuning on test. Mean interpolation RMSE mV at 5 mV noise:
|truth|calibrated|linear|RBF|oracle|
|---|---:|---:|---:|---:|
|null|.425010|.495165|.496025|.425018|
|rest|6.727447|.888706|.647822|.314001|
|peak|6.662336|1.532072|1.337774|.356226|

Mixed extrapolation at 5 mV: linear vs RBF rest 2.019111 vs 2.393884, peak 3.478151 vs 3.803782 mV. Same qualitative null and extrapolation limitations as v0.8.8. No unique mechanism claim. Full CI, Colab execution and merge pending.
