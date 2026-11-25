# v0.9.0a Colab reproduction audit and exploratory mesh repair

[Returned synthetic JSON](v090_summary.json), 38176 bytes. SHA256 7293e16504e11f2d0e23db9d2daf89883b5d7f02b9c0d7608893efe24d3f663d; Git blob ebb4aa22972dc326bceeb5b92008a92de9084e6d; exact GitHub byte readback verified. Source revision 1b73989fc730e02954e1187e9409e0da01fa31ff. Both reported SHA256 source hashes independently match original local files; corresponding GitHub blobs bfd2dc26f1aeb3929d452227bad3034140236d61 and c865881fdd3e5049304a3ef783a6144067ba1433. Original full local result SHA256 433aaea9ded4dcf53ab114cd5ec51b84826305144a418a887e6bd68a5cf9acd0. All 72 expected unique keys, optimizer successes, bounded closure states [0,0.9612629165]. Four targeted tests reported passed, stdout not supplied. Maximum per-fit differences vs original: test 0.000117270878 mV, extra 0.000296081743 mV, train 3.71111905e-8 mV, closure 7.6347222e-8. Null oracle amplitude is unidentifiable. No environment metadata in returned JSON.

Maximum normalized inventory residual 2.6091e-15, algebraic charge residual 1.3323e-15, max time-reference voltage difference 1.4673e-9 mV. These checks concern the reduced illustrative model, not full P2D mass/charge verification. Closure adds a terminal voltage correction and does not feed back into electrochemical fields.

## Mesh gate FAILED

| Profile | 8x12 -> 16x12 axial mV | 8x12 -> 8x24 radial mV | 8x12 -> 16x24 joint mV |
|---|---:|---:|---:|
|train|2.085903|6.376860|8.461339|
|test|1.390542|4.250362|5.639285|
|extra|2.781538|8.500088|11.276146|

Maximum absolute voltage differences; all exceed 1 mV. At 5 mV noise, same-mesh RBF test RMSE rest .647822 vs calibrated 6.727447, peak 1.337774 vs 6.662335, null .496025 vs .425010. Extrapolation RBF worse than linear at high noise: rest 2.393887 vs 2.019110, peak 3.803781 vs 3.478152. Same-mesh synthetic closure evidence does not show discretization-independent mechanism recovery.

## New exploratory local ablation (not Colab)
Read original solver and identified two candidate consistency repairs: reconstruct surface concentration with linear extrapolation of outer two shell averages at shell-volume centroids, keeping the conservative boundary source operator unchanged; include omitted fixed-current half-cell resistance at axial endpoints, (.25+.7)/(2*n) in normalized resistance units. Tested each independently and jointly, original unchanged. See [replay script](../../../scripts/v090_mesh_diagnostic.py). No fitting; all profiles at original physical parameters. Maximum voltage differences in mV:

|Variant|Profile|8x12 -> 16x12|8x12 -> 8x24|8x12 -> 16x24|16x24 -> 32x48|
|---|---|---:|---:|---:|---:|
|original|train|2.085903|6.376860|8.461339|4.407410|
|original|test|1.390542|4.250362|5.639285|2.937967|
|original|extra|2.781538|8.500088|11.276146|5.875066|
|radial|train|2.085797|3.365262|5.442669|1.934168|
|radial|test|1.390468|2.000165|3.331554|1.213662|
|radial|extra|2.781368|4.033241|6.366217|2.351541|
|axial|train|.176703|6.376860|6.441829|3.345964|
|axial|test|.113794|4.250362|4.319567|2.237007|
|axial|extra|.223579|8.500088|8.640238|4.474130|
|both|train|.176647|3.365262|3.216106|.820887|
|both|test|.113775|2.000165|1.947651|.497299|
|both|extra|.223560|4.033241|3.928110|1.002611|

Both: max mass residual 7.495e-14, charge residual 3.109e-15 across profiles and meshes. Joint fine-pair maximum reduced by about 82.9%; still strictly FAILS 1 mV. Exploratory correction is not yet approved: verify surface reconstruction under current switches, concentration bounds, independent reference, additional refinement, then regenerate independent fine-mesh synthetic data and repeat fitting with coarse/fine mismatch controls. Do not train AI to learn spatial discretization error. No CI, merge or experimental claim.
