# v0.8.9 Colab reproduction audit

User-returned [complete synthetic benchmark JSON](v089_summary.json), 168072 bytes. SHA256 e878247d095072531fd927235b673c3b943a148efe0b5046049b0d2ac870dbac, Git blob be8e2e9ceeb0f790d7c6fe779fb29c645ca3c9e7. Local file digest computed, GitHub byte-exact readback verified. Pinned source revision 8f665a002529b0ba29723245affc01d4887412c0. All four reported source hashes match original local source bytes and GitHub blobs. Original local JSON hash 52d06ffb278b4eb4955315d4d824613ae68058f75e033b116adb86f3f41c4ce3. Python 3.13.18 vs 3.13.5; NumPy 2.3.5/SciPy 1.17.0 both.

38 unique null calibration cases and 64 unique held-out cases, all expected keys; 306 fits implied by completed protocol, no per-fit calibration optimizer logs supplied. Four tests reported passed, stdout not supplied. All gain calculations, 18th order statistics, raw and gated selections independently recomputed from returned validation scores. Protocol matches original. All 64 raw and all 64 gated choices match original local report. Thresholds 0.01394656059783106 / 0.01366823412989282 at noise 1/5 mV; deltas -1.37655376e-9 / +1.22531629e-9. Maximum per-model held-out RMSE differences interpolation 5.57461558e-7 mV, mixed extrapolation 3.16194807e-6 mV, recovery 4.62187698e-7 mV, closure 2.07796753e-8 h^-1. Maximum reference state error 2.58756769e-7, all tested states in [0,0.865174567].

| Noise mV | Truth | Raw active /8 | Gated active /8 | Baseline interp mV | Gated interp mV | Baseline mixed extra mV | Gated mixed extra mV |
|---:|---|---:|---:|---:|---:|---:|---:|
|1|null|3|1|.065602432|.066642769|.164475587|.195516567|
|1|rest|8|8|1.727449007|.260596741|6.011323265|1.210451114|
|1|peak|8|8|1.157505232|.309755713|3.104933590|1.063936384|
|1|weak_rest|7|7|.422614782|.182448823|1.184248134|.544418597|
|5|null|4|1|.327848427|.332405687|.837657664|1.012397455|
|5|rest|6|6|1.773595422|.856243219|6.162117218|2.527064415|
|5|peak|5|4|1.166937404|.758304404|3.363332566|2.770430011|
|5|weak_rest|3|2|.540982069|.520000346|1.493377069|1.561749121|

Null false activation 1/8 per noise; 2/16 descriptive aggregate, paired seeds across noise. For 1/8, exact two-sided 95% binomial interval approximately 0.0032–0.5265 per noise under independent exchangeable test draws. Insufficient empirical precision to certify 10% false-activation target. Rank guarantee is marginal under exchangeability, not conditional on a particular calibration set or applicable to arbitrary real systems. No new threshold fitted. Weak alternative missed 6/8 at high noise; mixed extrapolation worsens in null and weak high-noise settings. Gate chooses linear or RBF closure, not necessarily a neural network. No unique mechanism identification, experimental validation, full P2D, or CI audit. No merge. Recommend independently enlarged null and alternative benchmarks and competing closure placements/observation-map mismatch prior to claiming robust discovery in P2D.
