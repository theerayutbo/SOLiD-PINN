# v0.9.0b Colab reproduction audit

[Complete returned synthetic JSON](v090b_summary.json): 112693 bytes, SHA256 0a30c47515f2050785636a123d6b3a8b3e42bf86b02327ddaaab51c857cd1e4d, Git blob e5fe74a57d79fb687775a63b5b4dd554aed5e35f. Byte-exact remote readback verified. Pinned source revision 1c6726d3d22fe945f961ce65a4f6f8aa62776f5e; all four source SHA256 values independently checked against executed local sources and corresponding remote Git blobs. Original local JSON SHA256 cc239e6d7fd8ddb4f6b35f4cba97c0a5f6ac15b4381c80839679f3b7199f95d6. Python 3.13.18 vs local 3.13.5, NumPy 2.3.5 and SciPy 1.17.0 both. Eight targeted tests reported by Colab; stdout not supplied. Local targeted tests independently rerun: 8 passed in 0.75 s.

216 unique expected keys (three truths, two noise levels, three seeds, three fitted meshes, four methods), 216 success flags; finite nonnegative RMSE values and finite fit parameters. Maximum per-fit absolute deltas vs local full JSON: test 0.000122323210 mV, extra 0.000357266507 mV, train 6.10657187e-8 mV, closure 1.55754837e-7. Maximum mesh delta cross-run difference 1.22390986e-9 mV.

## Numerical gate
Recomputed by explicit pair keys (32,48)->(64,96) and (64,96)->(128,192), not serialized dictionary ordering. All six comparisons <=1 mV. Maximum inventory and algebraic charge residuals 1.8707258e-13 and 5.7731597e-15 respectively; concentration ranges [0.19906685,0.82663159], surface [0.19757848,0.82811618]. Maximum adaptive time-reference voltage difference 7.8985707e-9 mV on 4x6 discretization. These verify selected reduced-model numerical checks only, not an independent continuum/full P2D reference.

| Joint refinement | train mV | test mV | extra mV |
|---|---:|---:|---:|
|8x12 -> 16x24|3.216106|1.947651|3.928110|
|16x24 -> 32x48|.820887|.497299|1.002611|
|32x48 -> 64x96|.204366|.123655|.249285|
|64x96 -> 128x192|.050827|.030725|.061940|

Approximately second-order voltage convergence on tested profiles; 128x192 is a numerical synthetic reference, not exact continuum truth.

## Closure learning with 128x192 generated reference
Means over three seeds at 5 mV noise.

| Truth | Fitted mesh | Calibrated test mV | Linear test mV | RBF test mV | Oracle test mV | Linear extra mV | RBF extra mV |
|---|---|---:|---:|---:|---:|---:|---:|
|null|8x12|.790695|.828764|.828339|.790689|2.035892|2.077870|
|null|32x48|.426268|.496359|.497312|.426263|1.549587|1.626644|
|null|128x192|.425010|.495165|.496025|.424979|1.546016|1.624836|
|rest|8x12|6.872904|1.041862|.900166|.720976|2.646330|2.862092|
|rest|32x48|6.734321|.885444|.646899|.314905|2.036339|2.398352|
|rest|128x192|6.727447|.888706|.647823|.314002|2.019110|2.393886|
|peak|8x12|6.875573|1.562441|1.411485|.751244|3.861401|4.228870|
|peak|32x48|6.673254|1.526281|1.333440|.358056|3.487205|3.813910|
|peak|128x192|6.662335|1.532072|1.337774|.356225|3.478151|3.803782|

Fine-mesh interpolation RBF improvement vs calibrated rest 90.37%, peak 79.92%; null worsens 16.71%. RBF remains worse than linear on high-noise extrapolation. Intermediate mesh has nearly the same mean RBF interpolation error as fine mesh for these profiles. Null-control 1 mV calibrated test drops from .655797 at 8x12 to .085594 at 128x192; RBF from .656911 to .100329. Refinement, not the AI, resolves most coarse-mesh null discrepancy. Same synthetic generator and closure structure; no unique missing-mechanism inference, no independent physical data, no claim that all discretization error is excluded. Closure is terminal voltage correction only, no feedback into reaction/transport fields. Adaptive gate not implemented in this version. No full CI audit or merge. Next: introduce local positive interfacial resistance into charge/reaction solve, verify mass/charge/energy and convergence for coupled states, compare null/competing mechanisms before enabling adaptive selection; experimental validation remains a separate gate.
