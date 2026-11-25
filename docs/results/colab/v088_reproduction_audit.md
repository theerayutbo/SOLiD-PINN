# v0.8.8 Colab reproduction audit

User-returned [complete synthetic benchmark JSON](v088_summary.json), SHA256 4fe7a64a8d0e739863ac834b9a15a3104d76a17d09f3ac4f6eface89efc54cfe, 122305 bytes. Git blob f4e95106c0717a13f0bdbb08f275a118ab0865a1; remote file readback exact. Source revision 43847936d96edc5f16f9692557face317155ecb9. All three reported source SHA256 values independently checked against original local sources. Original full local result hash 9294bd809699878e00b062d942ec2e09f5083ad890774f0232f3259bb449cc79.

108 distinct model evaluations; 180 distinct candidates (18 nominal fixed, 162 actual fitted), all success flags true. All selected lambdas minimize candidate validation RMSE and match original local selections. Protocol exactly matches local report. State range [0,0.8043550360], maximum reference error 9.68208013e-8. Five tests reported passed, independent Colab test stdout not supplied. Python 3.13.18 vs 3.13.5, NumPy 2.3.5 and SciPy 1.17.0 both. Maximum per-evaluation absolute deltas against original full local JSON: interpolation voltage RMSE 3.0100633e-7 mV, mixed extrapolation 1.3903680e-6 mV, recovery 3.1467382e-7 mV, closure RMSE 3.3401468e-8 h^-1, latent RMSE 1.2116245e-8.

## Colab means of three seeds, 5 mV noise
| Truth | Method | Interpolation mV | Mixed extrapolation mV | Recovery profile mV | Closure RMSE h^-1 |
|---|---|---:|---:|---:|---:|
|null|calibrated|.367413|.774022|.165549|0|
|null|linear|.474104|.837837|.477015|.007464|
|null|hybrid RBF|.511673|1.172558|.452213|.005516|
|rest|calibrated|1.771968|6.324691|1.886910|.039997|
|rest|linear|.779543|1.168979|.227802|.017975|
|rest|hybrid RBF|.555016|1.509341|.137303|.013587|
|rest|oracle|.467559|1.494154|.186165|.005227|
|peak|calibrated|1.007010|3.530419|.614772|.054029|
|peak|linear|.623761|1.322759|.343166|.026260|
|peak|hybrid RBF|.569016|2.335453|.352256|.023028|
|peak|oracle|.368570|.907121|.172077|.005715|

Hybrid improves held-out interpolation relative to calibrated incomplete physics but is inferior to linear closure on mixed extrapolation at 5 mV. Null control demonstrates spurious correction and poorer prediction. Rest truth d(0)=.100 h^-1, mean fitted RBF .093782 h^-1. Closure location and sign supplied; known voltage observation map, no unique mechanism identification, no experimental evidence, no collocation PINN.

## Exploratory model-class selection (post hoc; NOT prospective validation)
Choose lowest validation RMSE among calibrated, constant, linear and RBF, excluding oracle and privileged nominal. On six null scenarios, raw minimum selects an additional closure in three (one negligible numerical tie), including two RBF selections with relative validation improvements below 1%. At 1 mV all six non-null scenarios choose RBF; at 5 mV one peak scenario selects calibrated. A post-hoc 1% minimum relative validation improvement would suppress all null additions here, but also miss two of six non-null high-noise cases. This threshold must not be treated as calibrated; predeclare and test on independent seeds/truths with uncertainty and appropriate null false-positive control.

No CI or merge performed. Next: null-aware closure activation and competing mechanism identifiability on independent experiments.
