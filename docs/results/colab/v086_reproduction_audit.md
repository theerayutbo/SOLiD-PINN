# v0.8.6 Colab reproduction audit

User-returned synthetic results: [v086_summary.json](v086_summary.json).
SHA256 4f448f36476c8c312580186f24f47ba501eca2c2d1f0b569c24872c28fd4068c; 49,984 bytes; Git blob 26ed1795abb68783498364dd7fca6ef176570ffd. Local uploaded file hash computed, remote blob and bytes verified. Source revision 6879d8b4b9bec8ffac6ad800e911632a1788ae4e; source/test blobs match original reviewed Git objects f17e4fc7799ae46cef8bebb256dd6b0ef281ddad and 0b91630c4e8f254604065807a20901a45d7942c5. Reported source/test SHA256 match pinned notebook. All 60 unique expected combinations, 60 optimizer success flags, finite scalar metrics and reported state bounds [0,0.882196599]. Four targeted tests reported passed; test stdout not supplied. Reference RMSE 9.2588634e-8 / 7.4867753e-8.

Compared directly against original local full result JSON (SHA256 6d6acbcf98425d4db5ae875b81d9f5e377b0b3cbd21445223ea660346ed9fe53). Protocol identical. Python 3.13.5 vs 3.13.18; NumPy 2.3.5 and SciPy 1.17.0 both. No PyTorch used for this neural ODE. Non-neural maximum absolute interpolation / mixed extrapolation RMSE difference 2.21623e-7 / 1.07675e-6 mV. Neural ODE maximum differences 0.0340343 / 0.0137005 mV; 10/12 neural optimizer nfev counts differ, 0/48 non-neural. Numerical optimization sensitivity plausible, cause not isolated. 

| Noise (mV) | Method | CPU interp | Colab interp | CPU mixed extra | Colab mixed extra |
|---:|---|---:|---:|---:|---:|
|1|PCHIP|.218677|.218677|.727337|.727337|
|1|Neural ODE|.305705|.305761|.601695|.601779|
|1|Oracle|.094683|.094683|.210648|.210648|
|5|PCHIP|.683192|.683192|1.721328|1.721328|
|5|Neural ODE|1.876908|1.870763|3.617576|3.619003|
|5|Oracle|.452769|.452769|.958725|.958725|

Means of 6 fits per method/noise in mV. At 5 mV PCHIP interpolation 63.5% lower than neural ODE, despite virtually identical training RMSE (4.82733 vs 4.82747 mV). At 1 mV neural mixed extrapolation is better than PCHIP, but reverses at 5 mV. History at t=24h rational truth 7.531458 mV, stateless zero, PCHIP 7.772547, neural 7.765198 (1 mV). Rest voltage zero by construction. Two synthetic truths and three paired seeds, known observation map, no experimental validation or statistical superiority. Dynamic PINN not implemented in v0.8.6. No CI evaluated or main modified. Next: validation-selected rate regularization, independent noise/init seeds, dynamic PINN comparison, broader structural mismatch.
