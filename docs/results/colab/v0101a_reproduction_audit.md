# v0.10.1a — Colab reproduction audit

Original upload: SOLiD-PINN_v0101a_colab_0c30e05c3aa473e589cb.json, 9,901,975 bytes, SHA256 0c30e05c3aa473e589cbcf2807736b34f39eeedf3efc74dd0ca23ee924d2700b, Git blob identity da54d34834d81f140620963280b8deb0fd9a4b45. Original inspected directly in the local runtime. The full 9.9 MB raw file is not uploaded to GitHub; preserve the original upload for future raw audit. [Comparison audit JSON](v0101a_comparison_audit.json) is a derived archive of all 117 reported pairs, source identities, and key recomputed diagnostics, not a byte-exact copy of the raw trajectories. Derived JSON readback verified. Pinned source c488e2d7d20f57f2de99ca1ecb1f886bcd95680a: all five expected Git blobs independently verified. Reported hashes match notebook manifest. Eight targeted tests reported, stdout/runtime versions not in export. CI 45922297412 passed on pre-audit head d9cd48654d701cbf6cd3cec9173628d889634771.

## Independent checks of uploaded arrays
90 distinct expected stage keys; 201 finite increasing time samples, voltage and mean occupancy per stage, 201x7 finite surface and reaction probes. All reached intended events, voltage endpoint discrepancy <=8.89e-16 V, rest duration 1800 s. Current and capacity verified against independent nominal current convention; max capacity recomputation difference 2.85e-14 mAh/g. Recalculated inventory residual from mean occupancy, maximum discrepancy vs saved residual 1.46e-11 C/m2. All 60 consecutive mean-state differences zero. Full concentration state arrays are not exported, so independent array-level continuity and algebraic residual verification are unavailable. Source explicitly passes full state unchanged. Sampled bounds and reported residuals satisfy physical gate; max mass residual 1.06229e-7 C/m2, mixed algebraic residual 4.60076e-13, theta [.13544181,.83824240]. Bounds comparison allows 1e-12 rounding tolerance.

All 117 unique expected pair keys and six metrics per pair recalculated from raw saved traces at 201 common physical-time samples; maximum difference zero for all six metrics. 106/117 meet the voltage/capacity thresholds; failures retained. Fine 9/9 and final refinement 36/36 pass. Coarse/axial cross-solver 6/9 and 5/9; initial axial->radial refinement 14/18.

|Fine rate|Charge max mV|Rest max mV|Discharge max mV|
|---|---:|---:|---:|
|C/20|.020744910|.067369313|.027539702|
|C/10|.041967772|.134710455|.055588742|
|C/5|.087642393|.269283199|.115127293|

Fine max capacity delta .004440884%, endpoint .846928546 s, sampled surface occupancy .000198197687, reaction density RMSE 29.557304785 A/m3. Temporal refinement max .000292964 mV; final joint spatial refinement max .854842381 mV. Initial radial refinement max 2.040329796 mV. Fine capacities reproduce prior CPU rounded results within displayed precision. No full local trace rerun in this audit. FVM C/5 relative to C/20 charge 95.560599%, discharge 91.536529%. Different nominal rate under identical synthetic materials; not irreversible aging or Dessantis validation.

## Decision
Verified synthetic FEM/FVM spatial benchmark, not full electrochemical verification. Same BDF integrator and algebraic reaction formulation, linear illustrative OCV; no independent time-integrator proof. Probe comparisons are diagnostics, no predefined field acceptance thresholds, not full concentration/potential field validation. Shared equations may contain shared model-form error. Next: custom PyBaMM symbolic DAE and independent IDAKLU time integration, identical protocol; compare against frozen fine FEM/FVM and verify spatial/time convergence. COMSOL matched equations/parameters, primary source equation audit, material parameter calibration, ML/PINN and experimental validation remain outstanding. No merge into main.
