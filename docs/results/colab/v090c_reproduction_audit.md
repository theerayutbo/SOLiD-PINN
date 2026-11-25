# v0.9.0c Colab coupled closure audit

[Complete returned JSON](v090c_summary.json), 156062 bytes, SHA256 c1cb59463f25a11156dba208f5beb096e1c58eb1e8acf1e31d008ba8e612ed89; Git blob aeac4e3bcfe011adf5fc6627c0f1cd6816e995ad; byte-exact remote readback verified. Pinned source revision 966e4023927ceb2ad01cbf6a168978f04b9a1e50; all three reported source hashes independently match local source files and remote Git blobs. Python 3.13.18, NumPy 2.3.5, SciPy 1.17.0. Four tests reported passed (no stdout). All 72 unique expected truth/noise/seed/method keys, success flags and finite parameters/metrics. First full fitting run, not a reproduction of local fitting results (local numerical gates only). Nine numerical cases, 45 physical-check dictionaries, 216 post-fit check dictionaries, all healthy by independently recomputed thresholds. Both gates true. Maximum numerical delta difference versus local gate.json 2.13607e-10 mV.

## Numerical validation
Maximum spatial delta at equal temporal resolution .250078541128 mV; maximum temporal delta .005964657695 mV; direct fit/reference .243877893070 mV. All 45 comparisons <=1 mV. Across numerical and post-fit checks, normalized inventory residual <=2.05003e-13, algebraic charge residual <=2.22045e-15, resistive power identity residual <=7.95090e-15. Sampled bulk concentration [.19084811,.83155960], reconstructed surface [.18649988,.83781778], interface state [0,.96482837]; sampled dissipation nonnegative. This checks the reduced model and sampled states, not full thermodynamic energy conservation or all continuous-time states.

## Mean results across three seeds (mV for voltage)
|Noise|Truth|Method|Test RMSE|Extra RMSE|Closure RMSE (normalized inverse time)|
|---:|---|---|---:|---:|---:|
|1|null|calibrated|.09070929|.30751451|0|
|1|null|linear|.10442036|.31359771|.00131968|
|1|null|rbf|.10468535|.32751446|.00107079|
|1|null|oracle|.09071654|.30753783|0|
|1|rest|calibrated|3.96984606|9.27517531|.15998921|
|1|rest|linear|.32586270|.83020476|.01572691|
|1|rest|rbf|.15871776|.55899184|.01100504|
|1|rest|oracle|.07215652|.19362565|.00122675|
|1|peak|calibrated|3.99855339|7.68458227|.22957476|
|1|peak|linear|.70875919|1.61772550|.04983497|
|1|peak|rbf|.59946831|1.49678072|.03272551|
|1|peak|oracle|.08163298|.23875643|.00430344|
|5|null|calibrated|.42017871|1.51203063|0|
|5|null|linear|.49051676|1.53444257|.00681079|
|5|null|rbf|.49054136|1.61619926|.00557863|
|5|null|oracle|.42033452|1.51261087|0|
|5|rest|calibrated|3.99510098|9.43737142|.15998921|
|5|rest|linear|.72978429|1.76833159|.04550540|
|5|rest|rbf|.54018971|2.12263932|.04045802|
|5|rest|oracle|.30429559|.89724294|.00595977|
|5|peak|calibrated|3.96963748|7.84396718|.22957476|
|5|peak|linear|1.03645429|2.55739874|.06797128|
|5|peak|rbf|.96668596|3.21545237|.06210238|
|5|peak|oracle|.34350486|1.11788209|.02135984|

Sum of reported fit wall times 401.3447 s (includes post-fit diagnostics, excludes numerical gate and setup). RBF improves test RMSE at 5 mV by 86.48% rest and 75.65% peak, worsens null by 16.75%; high-noise extrapolation inferior to linear. Null means no extra recovery law, not zero interface resistance. Known generator structure, fixed spatial pattern, global interface state; voltage-only fit; fixed-basis RBF not collocation PINN. Does not establish unique mechanism identification, internal-state recovery accuracy, full P2D or experimental validation. No adaptive gate in this version. Next suggested step: prospective validation-only closure selection with independent null calibration on coupled model, competing mechanism/observation mismatch and quantitative internal-field errors vs fine reference. CI/merge not performed.
