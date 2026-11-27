# v0.9.0b — corrected mesh bridge and fine-reference closure learning

Executed 216 fits, all succeeded. Eight local regression tests passed (four new and four inherited). Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0. Full local result SHA256 cc239e6d7fd8ddb4f6b35f4cba97c0a5f6ac15b4381c80839679f3b7199f95d6. Source/test Git blobs verified against executed files. No CI/Colab replay or merge yet.

Correct surface concentration by linear reconstruction from the two outer spherical shell averages using volume centroids. Retain conservative outer flux injection. Add omitted axial endpoint half-cell resistance. Diagonalize symmetric current projection P to propagate n independent m-dimensional radial blocks by matrix exponential instead of an (nm)-dimensional dense exponential. No change to closure parameterization. Independent DOP853 time integration in original coordinates at 4x6 agrees within 7.895e-9 mV (same semi-discrete operators, not independent spatial reference).

Maximum absolute voltage differences (mV):
|Profile|8x12->16x24|16x24->32x48|32x48->64x96|64x96->128x192|
|---|---:|---:|---:|---:|
|train|3.216106|.820887|.204366|.050827|
|test|1.947651|.497299|.123655|.030725|
|extra|3.928110|1.002611|.249285|.061940|

Gate: both final adjacent mesh pairs <=1 mV for all profiles; PASS. Observed approximately second-order joint refinement, not proof of continuum accuracy. Max normalized mass residual 1.478e-12 and charge residual 5.774e-15; sampled concentration range .199067–.826632, surface .197578–.828116. No continuous-time maximum principle proof.

All synthetic observations generated at 128x192. Compare 8x12 stress, 32x48 independent coarser discretization and same-fine control, three truths null/rest/peak, two noise SDs 1/5 mV, three seeds 11/23/37, four methods calibrated/linear/RBF/oracle. Same voltage noise and profiles per comparison; no test labels used in fit; same regularization as v0.9.0a. Known electrochemical parameters, terminal correction only. Fine reference is the same corrected equation/discretization family, not independent external solver or experiment.

At 5 mV noise, 32x48 mean interpolation RMSE (mV) calibrated/linear/RBF/oracle: null .426268/.496359/.497313/.426252, rest 6.734321/.885443/.646900/.314907, peak 6.673254/1.526280/1.333440/.358056. RBF reduces rest/peak error versus calibrated by 90.4%/80.0%; null worsens. Same-fine RBF .496025/.647822/1.337774; close to coarser result. At 5 mV mixed extrapolation linear beats RBF for rest 2.036338 vs 2.398358, peak 3.487202 vs 3.813913. Closure RMSE at 32x48 RBF .003132/.026952/.045342 per hour, not unique mechanism recovery. No general neural superiority, no adaptive gate in this benchmark (deferred to separately calibrated protocol), no fully coupled P2D or experimental validation. Next: coupled interface kinetics, independent reference, adaptive gate under discretization mismatch and actual measurements. 
