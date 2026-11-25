# v0.9.0d Colab audit — prospective adaptive coupled closure

[Full returned synthetic JSON](v090d_summary.json), 1044209 bytes, SHA256 d6ae9d75d20e30f095bcdacaffdfaa4aa251205ec56b76969515ad39b1880175, Git blob ea6515efc0cc2ac64804cc4338bc4cd9b07681c0. Byte-exact GitHub readback verified. Pinned source revision f9aded427d46bfbd9b0ea829d3e909613aaa9d33. All five reported source SHA256 values match local source files and corresponding verified Git blobs. Python 3.13.18, NumPy 2.3.5, SciPy 1.17.0. Eight targeted tests reported (stdout unavailable). First full benchmark run, not an independent rerun of the full fit campaign.

## Completeness and numerical checks
38/38 unique calibration keys, 64/64 unique held-out keys, 306/306 successful candidate fits. Independently recomputed all gains, raw choices, thresholds and 64 gated selections. All 1,705 reported physical-check dictionaries (45 nominal, 664 randomized truth, 996 fit) satisfy original criteria. Maximum normalized inventory residual 2.06668016e-13; algebraic charge 3.10862447e-15; resistive power identity 8.08242904e-15. Sampled bulk concentration [.18924433,.83266673], surface [.18591958,.83770902], interface state [0,.97028597]. Maximum nominal mesh/time delta .250078541128 mV, randomized direct fit-reference .244323186281 mV. All <=1 mV. These are sampled reduced-model checks, not full thermodynamic validation.

## Prospective gate results
Thresholds recomputed from 18th order statistic of 19 calibration gains: 1 mV .01116895509752136; 5 mV .01143051368178627. At each noise level raw null activation 4/8 and gated 1/8; rest, peak and weak_rest 8/8 both raw and gated. The sole gated null activation is seed 2001 (linear) at both noise levels. Paired seeds across noise/truth, so pooled 2/16 null and 48/48 nonnull are descriptive only. Exact two-sided 95% binomial interval for 1/8 approximately 0.32–52.65%; observed 12.5% does not certify <=10%. For 8/8 the corresponding interval is approximately 63.1–100%. Marginal rank target assumes exchangeable null scores and successful gates; not a guarantee conditional on fixed calibration or real cells. No threshold retuning on test set.

Means per stratum over eight seeds. Voltage RMSE in mV; reaction density RMSE in normalized units.
| Noise | Truth | Baseline test | Gated test | Baseline extra | Gated extra | Baseline test reaction density | Gated test reaction density |
|---:|---|---:|---:|---:|---:|---:|---:|
|1|null|.068601088|.069884257|.148335784|.151260871|.000016713|.000017152|
|1|rest|4.041666054|.169648427|9.340207883|.545389666|.000760109|.000032113|
|1|peak|4.097442232|.604212715|7.769677541|1.432745324|.000759005|.000094318|
|1|weak_rest|1.212879431|.127230043|2.379942263|.255312950|.000170136|.000020969|
|5|null|.310352641|.317892156|.690006616|.704704710|.000066912|.000068953|
|5|rest|4.059766793|.551215515|9.322553200|1.314241891|.000762715|.000121730|
|5|peak|4.108528603|.875771569|7.778665491|2.077797261|.000761345|.000166948|
|5|weak_rest|1.253682226|.568031293|2.432582836|.867835574|.000182083|.000090472|

At 5 mV gated mean test voltage error reduction vs baseline 86.42% rest, 78.68% peak, 54.69% weak; test reaction-density reduction 84.04%, 78.07%, 50.31%. Null worsens 2.43% voltage and 3.05% reaction density. Gate reduces false activation, but null extra RMSE (.704705) is slightly worse than raw (.700829). Fixed RBF has smaller mean peak/weak test RMSE at 5 mV (.859862/.542991 vs gated .875772/.568031); linear has smaller mean rest/peak extra RMSE (1.269704/2.063782 vs gated 1.314242/2.077797). Adaptive selection is not universally best. Gated selected linear/RBF counts at 5 mV rest 4/4, peak 2/6, weak 2/6. At 1 mV rest 1/7, peak 0/8, weak 4/4. The weak case is a known 15% amplitude synthetic rest law; no cross-version performance attribution because simulator, amplitudes and profiles changed. Reaction-density error is compared with same-equation fine reference, not experimental fields. Fixed spatial pattern and global history state; no unique mechanism identification, competing mechanism placements, observation mismatch, real battery validation, full P2D or collocation PINN.

Next: preregister robust null/alternative tests with independently enlarged samples and competing mechanisms (transport/kinetics/voltage-map mismatch), non-IID noise and different profiles. Design real pulse/rest measurements and external data validation only after these checks. No full benchmark replication or CI/merge assertion in this audit.
