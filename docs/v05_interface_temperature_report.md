# v0.5 research report — Li|LPSCl ASR and temperature scenarios

**Date:** 2026-11-23. **Status:** exploratory reduced-P2D study; NOT a verified Dessantis reproduction. The numerical targets below are **locally digitised** from the user's Dessantis PDF Figures 4 and 5, NOT author-supplied raw laboratory measurements. The CSVs are not committed to GitHub because permissions to redistribute derivative data need review.

## 1. Published sources (exact provenance)

- **Dessantis et al. (2024)**, *Investigating sulfide-based all solid-state cells performance through P2D modelling*, Chemical Engineering Journal Advances **18**, 100610. DOI: [10.1016/j.ceja.2024.100610](https://doi.org/10.1016/j.ceja.2024.100610). Fig. 2 and §4.1.2 report Li6PS5Cl conductivity **1.6 mS/cm at 25°C** and **4.3 mS/cm at 50°C**; Table 2 reports **0.43 S/m** at 50°C and NMC diffusion **2e-13 m²/s**. Figure 4 is pseudo-OCV; Fig. 5 contains C/20 calibration and C/10,C/5 validation profiles. Article CC BY-NC-ND 4.0.
- **Narayanan et al. (2022)**, *Effect of current density on the solid electrolyte interphase formation at the lithium|Li6PS5Cl interface*, Nature Communications **13**, 7237. DOI: [10.1038/s41467-022-34855-9](https://doi.org/10.1038/s41467-022-34855-9). Figs. 3–4 distinguish charge transfer and SEI resistive components and current-dependent interface evolution. **Motivates** an optional contact ASR; no numerical priors are imported.
- **Singh, Fuchs, Krempaszky, Mogwitz & Janek (2023)**, *Non-Linear Kinetics of The Lithium Metal Anode on Li6PS5Cl at High Current Density*, Advanced Science **10**, 2302521. DOI: [10.1002/advs.202302521](https://doi.org/10.1002/advs.202302521). Reports a ~**0.8 Ω cm²** polarization resistance for its microelectrode conditions. Used **only** as a contextual sensitivity scenario, **not** transferred or fit as a parameter of Dessantis's coin cell.
- **Sulzer et al. (2021)**, *Python Battery Mathematical Modelling (PyBaMM)*, JORS **9**. DOI: [10.5334/jors.309](https://doi.org/10.5334/jors.309); [official custom half-cell tutorial](https://docs.pybamm.org/en/latest/source/examples/notebooks/creating_models/5-half-cell-model.html). Candidate independent framework, **not run in v0.5** because pybamm was unavailable and pip access failed.

BibTeX entries are in [v05_references.bib](v05_references.bib) and previous references in [../CITATIONS.bib](../CITATIONS.bib). Earlier Puls/Schomburg/IMOTHEP studies are screened in [cross_study_evidence.md](cross_study_evidence.md). None of their original raw measurement arrays were imported into this v0.5 test.

## 2. New physics

An optional **lumped** series Li|LPSCl area-specific resistance (ASR) introduces a terminal voltage shift **ΔV = −J·ASR**, where signed J=I/A in A/m² and ASR in Ω·m². For charge J is negative (voltage increases); for discharge it is positive (voltage decreases). It changes voltage and cutoff but, at fixed state, not the local cathode reaction currents. Default=0 preserves the v0.4 solver. This is not a detailed pressure-dependent SEI/contact evolution model.

SSE conductivity is computed by **kappa(T)=kappa(323.15K) exp[−Ea/R·(1/T−1/323.15K)]**. The *two-point* Dessantis EIS-derived activation energy is **31.676 kJ/mol**. It is not a multi-temperature regression. NMC diffusion activation is optional/hypothetical; OCV, Butler–Volmer j0, contact effects and all other thermal parameters remain fixed.

| Temperature | Predicted SSE kappa |
|--|--:|
| 25°C | 0.1600 S/m (input) |
| 40°C | 0.2951 S/m (interpolated) |
| 50°C | 0.4300 S/m (input) |

## 3. ASR ablation: C/20 training ONLY

Fixed previous v0.3 C/20 parameters: **cathode j0 = 0.0566011934 A/m²**, **initial SoC = 0.0770454572**. No refit of those parameters in v0.5. Six ASR values were predeclared: 0, 0.8, 5, 50, 200, 500 Ω cm². Only the **C/20 voltage residual plus duration penalty** chooses ASR; C/10 and C/5 are held out. Mesh nx=4, nr=6, dt=300 s.

| ASR (Ω cm²) | C/20 charge RMSE (mV) | C/20 discharge RMSE (mV) | Composite training objective (approx) |
|--:|--:|--:|--:|
| 0 | 52.41 | 95.11 | 0.006021 |
| 0.8 | 52.44 | 95.10 | 0.006021 (greater unrounded) |
| 5 | 52.60 | 95.09 | 0.006021 (greater unrounded) |
| 50 | 54.38 | 95.11 | 0.006064 |
| 200 | 60.32 | 98.40 | 0.006638 |
| 500 | 72.83 | 113.85 | 0.009316 |

**Selected ASR=0 Ω cm² among the predeclared grid.** This **does not demonstrate zero physical interface resistance**: j0, phase fractions, contact pressure, other kinetic parameters and digitisation uncertainty are not independently identified. No high-rate accuracy improvement can be claimed.

### Held-out results (selected scenario = original baseline)

| Rate | Charge RMSE | Discharge RMSE |
|--|--:|--:|
| C/10 | 50.78 mV | 177.69 mV |
| C/5 | 81.32 mV | 209.05 mV |

Four-stage mean RMSE = **129.71 mV** both before/after selected ASR.

### Numerical resolution sensitivity

| nx / nr / dt | C/20 charge / discharge RMSE (mV) | C/5 charge / discharge RMSE (mV) |
|--|--|--|
| 4 / 6 / 300s | 52.41 / 95.11 | 81.32 / 209.05 |
| 6 / 10 / 150s | 52.43 / 95.05 | 81.30 / 209.05 |
| 8 / 16 / 75s | 52.45 / 95.00 | 81.26 / 209.05 |

These selected summary metrics differ by about **0.1 mV or less** across the tested discretisation settings. This supports stability *of those metrics* but is not a proof of fully converged fields or an independent full-P2D implementation.

## 4. Reproduction / remaining gates

Install dependencies and run tests before the sensitivity driver:

```bash
pip install -e '.[dev,pinn]'
python -m pytest -q tests/test_transfer_v05.py
python scripts/interface_temperature_sensitivity.py \
  --charge-ocv /private/charge.csv --discharge-ocv /private/discharge.csv \
  --c20 /private/c20.csv --c10 /private/c10.csv --c5 /private/c5.csv \
  --outdir outputs/interface_temperature
```

Experimental-curve schema: `time_h,voltage_v,stage`; OCV schema: `soc,voltage_v` for both charge/discharge branches. The driver writes training objective, held-out diagnostic CSV, temperature scenario and provenance JSON locally.

**Blocked:** independent custom PyBaMM/FEM validation (PyBaMM install could not resolve package-index DNS in the current environment), raw Dessantis measurements, matched pressure-dependent EIS, joint parameter identifiability/uncertainty and fully temperature-dependent electrochemistry. Do not use the standard liquid-electrolyte DFN as proof of equivalence to the article's single-ion SSE. Issue #2 remains open.

**Conclusion:** v0.5 improves auditability, adds a physically interpretable *optional* term and validates numerical insensitivity on tested grids, but **does not improve predictive accuracy**. Report this negative result rather than silently re-tune on held-out C/10 or C/5.
