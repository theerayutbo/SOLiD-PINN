# v0.8.1 — LiOPA ASR qualification and exploratory temporal benchmark

Source: Fadillah et al., Advanced Materials, DOI https://doi.org/10.1002/adma.202515013; open data https://doi.org/10.5281/zenodo.17816356 (CC BY 4.0). The submitted evidence ZIP has SHA-256 219d95bee956a186e4e99821e44c4b64f165bd6bc76c2c11e9d67a5c26d90ce1. All 12 exported files match their supplied manifest hashes, and four source workbook/CSV identities agree with the prior inventory. Source workbook bytes are not present in this ZIP, so the original workbook hashes cannot be independently recalculated here. No raw files committed.

## Observations
Supporting Information, Li SP & ASR S9 S10: three four-column groups, time h, voltage mV, ASR ohm cm2, current mA/cm2. Exclude missing values and |j| <= 1e-6; retain repeated rounded timestamps (376/2549/7592 repeated times, respectively). Each group is one published trace, not thousands of independent specimens. No failure labels inferred from trace end times. The paper reports >400 h stable Li-OPA symmetric cycling at nominal 1 mA/cm2; distinct Li6PS5Cl0.5Br0.5 material, not Dessantis Li6PS5Cl. 

ASR is derived, not an independent target: |V|/(2|j|) agrees with the exported ASR within 0.000109 ohm cm2 across all groups. The factor two is consistent with symmetric cell normalization, but does not isolate one interfacial mechanism or remove bulk/other losses. Do not add it as an independent loss against the same voltage points or transfer it into full-cell P2D as a measured cathode interface coefficient. EIS S5 contains real/imaginary impedance pairs but no frequency axis. No frequency-dependent circuit fit. Full-cell NMC811 chemistry remains separate.

## Exploratory baseline
Equal-weight hourly median bins, floor(time_h). Fit constant (mean) and linear OLS to bins 1–29; evaluate bins 30–49 without refitting. Exclude startup bin 0 and boundary bin 50 for common observation horizon. Raw-point median for t<50 reported separately. This protocol was chosen during exploratory inspection, not prospectively preregistered; holdout is within the same traces and not independent cell/material validation. No extrapolation of negative ASR predictions into physical model. Units ohm cm2 except time and slope (ohm cm2/h).

| group | valid ASR observations | last hour | median t<50 | constant test RMSE | linear test RMSE |
|---|---:|---:|---:|---:|---:|
| Pristine | 5327 | 50.00 | 1.99969 | 0.70301 | 1.64541 |
| 2 OPA | 17277 | 147.77 | 35.20000 | 0.43531 | 1.71208 |
| 2 Li-OPA | 47684 | 401.41 | 17.89437 | 0.82020 | 0.79063 |

Constant wins in two groups; linear has a small advantage for Li-OPA. Do not infer statistical significance from correlated observations. Li-OPA has a higher early median than pristine, lower than OPA; this is not proof of a causal durability effect. Long-horizon frozen-fit diagnostic (hours 50–99, 100–139, 140–399): Li-OPA constant RMSE 1.69245/2.02456/2.68417, linear 1.62267/1.91747/2.40837; OPA constant 1.38246/3.49470/5.13779, linear 4.57606/8.33199/2.13288 (last OPA bin group only 7 complete-hour-index bins). This is adverse evidence against one generic linear aging law.

Humidity conductivity data, relative to initial 100%: at 12/24 h pristine 55.2/33.5%, 2 OPA 88.9/86.3%, 2 Li-OPA 94.9/92.9%. These are separate exposure conditions, not synchronized with the symmetric cycling trace; no joint time-dependent law inferred.

## Decision
Use the constant ASR model as a simple comparator, not a validated physical law. Advance to a symmetric-cell observation model with signed current, separated bulk/interface/kinetic losses, explicit treatment and protocol metadata; require independent EIS frequency or geometry/transport data before identifying each term. Use cycle-blocked and cross-cell/study tests where available. Consider separate positive constrained dynamic ASR candidate after defining physically justified state variables. Do not call this a PINN training result or add the symmetric ASR directly to Dessantis.

The calculations were actually executed in Python (pandas 2.2.3, NumPy 2.3.5, SciPy linregress). The accompanying replay script transcribes the executed procedure; exact repository script and CI have not been executed. Run with authorized submitted evidence ZIP:
```bash
python scripts/analyze_liopa_asr.py /private/SOLiD-PINN_open_evidence.zip --out /private/asr_metrics.json
```
