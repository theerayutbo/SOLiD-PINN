# v0.4 — Independent NMC622 OCV cross-study ablation (23 Nov 2026)

**Scientific status: exploratory; NOT full P2D reproduction.**
The Dessantis pseudo-OCV charge/discharge functions and charge/discharge
traces were digitised locally from the user's PDF. The CSVs are not author raw
measurements and are not republished in this public repository. These metrics
inherit line-thickness, endpoint and stage-time-registration uncertainty.

## Sources and exact role

1. **Dessantis et al.** (2024), *Investigating sulfide-based all solid-state
   cells performance through P2D modelling*, Chemical Engineering Journal
   Advances 18, 100610. DOI https://doi.org/10.1016/j.ceja.2024.100610
   Fig. 4: source cell pseudo-OCV at 50°C (C/30), both charge and discharge;
   Fig. 5: digitised target voltages for C/20, C/10, C/5.
   PDF states CC BY-NC-ND 4.0; no derived curves distributed here.

2. **IMOTHEP Consortium / KIT and AIT** (2023), *D4.9: Final Battery Model
   Documentation*, Table 3, p.12.
   https://www.imothep-project.eu/files/d4-9-final-battery-model-documentation.pdf
   Independent NMC622 single-valued OCV curve based on AIT measurements.
   In lithium stoichiometry x=c_s/c_s,max, whereas SOLiD-PINN uses soc=1-x.
   IMOTHEP's simulated cell uses a different electrolyte and its table
   lists a different temperature (60°C). The publicly available PDF itself
   contains a **proprietary rights notice** on p.2. Only the numerical
   formula is used; no original measurement series is republished.

3. **Puls, Nazmutdinova, Kalyk et al.** (2024), *Benchmarking the
   reproducibility of all-solid-state battery cell performance*, Nature
   Energy 9, 1310–1320, https://doi.org/10.1038/s41560-024-01634-3 .
   21 labs, NMC622 / Li6PS5Cl and **In/(InLi)x anode**, different pressure,
   loading and cell conditions. Source Data Supplementary Figs. 11–27
   XLSX available; CC BY 4.0. **Screened; not ingested or fitted here.**

4. **Schomburg, Schmidt and Röder** (2025), *Interaction between Formation
   Protocol and Electrolyte Composition during Solid-Electrolyte Interphase
   Formation: A Model-Supported Investigation - Dataset*, Zenodo:
   https://doi.org/10.5281/zenodo.15688067 . Includes
   `pocv_ref.zip/pocv_ref_NMC622.mat` with intercalation/deintercalation
   reference curves. Measurements use liquid electrolyte at **40°C**;
   CC BY 4.0. URL verified, binary download unavailable in this runtime:
   **not ingested or fitted here**.

5. **Narayanan et al.** (2022), *Effect of current density on the solid
   electrolyte interphase formation at the lithium|Li6PS5Cl interface*,
   Nature Communications 13, 7237,
   https://doi.org/10.1038/s41467-022-34855-9 .
   Evidence that the interface impedance changes with Li deposition
   current density; **no EIS numerical parameters fitted here**.

Machine-readable references: [CITATIONS.bib](../CITATIONS.bib).
Data status: [external_data_registry.csv](external_data_registry.csv).

## Predeclared test, not physical mixing

For each stage, `U_test = (1-w) U_Dessantis + w U_IMOTHEP` with
fixed external weight `w` of **0**, **0.25**, or **0.50**.
This is a controlled sensitivity experiment, NOT a measured mixture.
The IMOTHEP equation does not have charge/discharge hysteresis: mixing it
into the paper's *pseudo*-OCV artificially suppresses that hysteresis.
The true electrode stoichiometric operating window is not reconciled.
Therefore no fitted `w` is presented as a physical parameter.

Only cathode exchange-current density and assumed initial SoC were fitted
on digitised **C/20**. The fitted parameters were then frozen.
C/10 and C/5 were held out. Numerical settings:
`nx=4, nr=6, dt=300 s, max_nfev=25`. Report both voltage RMSE and
stage-duration mismatch; some model endpoints differ by >1 hour.
**Do not choose w after inspecting the held-out C-rates.**

### RMSE in millivolts (lower is better)

| OCV | C/20 charge | C/20 discharge | C/10 charge | C/10 discharge | C/5 charge | C/5 discharge | Mean 4 held-out |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dessantis only | 52.41 | 95.11 | 50.78 | 177.69 | 81.32 | 209.05 | **129.71** |
| IMOTHEP 25% | 16.11 | 134.42 | 53.29 | 172.74 | 109.38 | 192.39 | 131.95 |
| IMOTHEP 50% | 41.41 | 150.23 | 91.60 | 166.12 | 155.95 | 179.70 | 148.34 |

**Outcome:** Independent OCV does not improve the predeclared *mean
held-out* voltage RMSE. The 25% blend is 1.7% worse and 50% blend
14.4% worse, despite a strongly improved *training* charge trace at
25%. This is evidence of domain-shift risk, not evidence that a
particular material property has been precisely inferred.

All validation remains limited by:
- Source figure digitisation uncertainty, especially near steep cutoffs
- Unmatched operating temperature, electrode chemistry and usable SOC
- Not-yet-verified PyBaMM/FEM full coupling
- Unquantified parameter identifiability, noise and numerical convergence

## Reproduce with authorized input CSVs

```bash
python scripts/compare_cross_study_ocv.py \
 --charge-ocv /private/ocv_charge.csv \
 --discharge-ocv /private/ocv_discharge.csv \
 --c20 /private/trace_C20.csv \
 --c10 /private/trace_C10.csv --c5 /private/trace_C5.csv \
 --nx 4 --nr 6 --dt 300 --max-nfev 25
```

### Next data gates

Import the real NMC622 intercalation/deintercalation arrays from
Schomburg; build a separate In/InLi cell adapter for Puls; quantify
Li/LPSCl interfacial resistance under matched conditions; request
original Dessantis voltages and validate with a separately implemented
custom PyBaMM/FEM model. Do not use a standard liquid-electrolyte DFN
without modifications.

## Additional parameter-transfer probe: cathode diffusivity

IMOTHEP D4.9 **Table 2, PDF p.11** reports NMC622 solid diffusivity
`D_s=4.84e-14 m^2/s` for its different AIT cell, compared with the
`D_s=2.0e-13 m^2/s` value in Dessantis (2024) Table 2 (p.5).

We substituted ONLY this externally reported diffusivity, kept the original
Dessantis-derived charge/discharge pseudo-OCV, and refitted just cathode
exchange-current density and initial SoC at C/20 as before.
**C/10 and C/5 were left held out.**

| Case | C/20 charge/discharge RMSE | C/10 charge/discharge RMSE | C/5 charge/discharge RMSE | Mean 4 held-out |
|---|---|---|---|---|
| Dessantis D_s | 52.41 / 95.11 mV | 50.78 / 177.69 mV | 81.32 / 209.05 mV | 129.71 mV |
| IMOTHEP D_s | 51.62 / 93.87 mV | 50.32 / 177.55 mV | 81.11 / 209.07 mV | **129.51 mV** |

The mean held-out difference is about **0.20 mV (0.15%)**, well below
the uncertainty of digitised plots and likely below numerical-scheme
uncertainty. **Do not report this as a meaningful physical improvement or
a reliable estimate of the target cell's D_s.** The true electrode
diffusivity can depend on stoichiometry, temperature and fabrication.

Reproduce with the same private input CSVs:

```bash
python scripts/compare_diffusivity_prior.py \
  --charge-ocv /private/charge.csv --discharge-ocv /private/discharge.csv \
  --c20 /private/c20.csv --c10 /private/c10.csv --c5 /private/c5.csv
```
