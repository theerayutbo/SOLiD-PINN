# Calibration experiment ledger — accepted, rejected, and inconclusive trials

**Updated:** 2026-11-23. **Scope:** v0.3–v0.5 exploratory reduced-P2D sensitivity experiments. This ledger preserves **negative results** rather than presenting only improved training fits. It is an audit of *previously executed local runs*; it is **not** a new calibration or independent rerun. Machine-readable metrics: [calibration_trial_metrics.csv](calibration_trial_metrics.csv). Original run records and additional details: [v0.4 evidence](cross_study_evidence.md), [v0.5 report](v05_interface_temperature_report.md) and the locally generated v0.4/v0.5 result packages.

> **Scientific gate:** the reference voltage/OCV points were **digitised from figures**, not supplied as raw experimental data by the authors. The source paper has a CC BY-NC-ND licence; image and derived numeric arrays are intentionally **not committed publicly**. We cannot claim reproduction of the published Fig. 5 or Table 3 capacity-error targets, even if a particular local-fit metric falls.

## Protocol and scores

- Primary cell: **Li metal | Li6PS5Cl | NMC622** from [Dessantis et al., 2024](https://doi.org/10.1016/j.ceja.2024.100610). Local reconstructions of **Fig. 4** charge/discharge pseudo-OCV and **Fig. 5** voltage-time curves are used only in private numerical runs.
- **Calibration** uses C/20 *only* (two stage curves). **C/10 and C/5** are frozen-parameter hold-outs (charge/discharge).
- Aggregate score here is the simple arithmetic **mean of four held-out stage voltage RMSEs in mV**. This gives each stage equal weight, not each observed point. Duration discrepancies are separate and can exceed one hour. It is **not** the published article's capacity-error metric.
- The software remains a reduced numerical prototype. No independent full coupled PyBaMM/FEM equivalence, experimental uncertainty or robust parameter identifiability study is established. **We do not choose weights, coefficients or resistances using held-out outcomes.**

## 1. Original C/20 fitting (v0.3)

The starting assumed-kinetics model had approximately **62.4 mV** charge and **140.6 mV** discharge RMSE on C/20. Fitting **cathode exchange current density** (about `0.056601 A/m²`) and **assumed initial SoC** (about `0.077045`) to C/20 reduced those errors to **52.41 mV** and **95.11 mV**. These values are **not independently measured material constants**; time-origin, pseudo-OCV endpoints and parameter identifiability remain uncertain.

After freezing this fit, C/10 errors were **50.78/177.69 mV** (charge/discharge) and C/5 errors **81.32/209.05 mV**, giving a **129.71 mV** mean held-out score. This fitted baseline is the comparator below, **not** an experimentally validated ground truth. See [v0.3 calibration protocol](calibration_protocol.md) and [PR #3](https://github.com/theerayutbo/SOLiD-PINN/pull/3).

## 2. Independent NMC622 OCV blending — tried, **not adopted** (v0.4)

External source: **IMOTHEP D4.9** (AIT measurements / KIT OCV equation), [report PDF](https://www.imothep-project.eu/files/d4-9-final-battery-model-documentation.pdf), **Table 3**. IMOTHEP operates at different temperature, electrolyte and electrode stoichiometric window, and its single-valued OCV lacks Dessantis's stage-dependent pseudo-OCV hysteresis. The test `U=(1-w)U_Dessantis+wU_IMOTHEP` is an **arbitrary sensitivity ablation, not a physically calibrated material mixture**.

| Trial | C/20 charge/discharge RMSE (mV) | C/10 charge/discharge (mV) | C/5 charge/discharge (mV) | 4-stage held-out mean (mV) | Decision |
|---|---:|---:|---:|---:|---|
| Dessantis OCV only; `w=0` | 52.41 / 95.11 | 50.78 / 177.69 | 81.32 / 209.05 | **129.71** | **Retain baseline** |
| IMOTHEP 25%; `w=.25` | 16.11 / 134.42 | 53.29 / 172.74 | 109.38 / 192.39 | 131.95 | **Rejected** (held-out score worsened 1.7%) |
| IMOTHEP 50%; `w=.50` | 41.41 / 150.23 | 91.60 / 166.12 | 155.95 / 179.70 | 148.34 | **Rejected** (held-out score worsened 14.4%) |

The tempting **16.11 mV** result was *training-only charge*, while training discharge rose to **134.42 mV**. Selecting this trial because its training charge looks better would be misleading. The C/10/C/5 hold-outs disfavor these blends under the stated aggregate metric. Detailed held-out coverage and stage-duration diagnostics are in [cross-study evidence](cross_study_evidence.md).

## 3. External cathode solid diffusion coefficient — **inconclusive / not adopted** (v0.4)

- Dessantis **Table 2:** `D_s=2.0e-13 m²/s`.
- IMOTHEP D4.9 **Table 2** (unmatched AIT NMC622 cell): `D_s=4.84e-14 m²/s`.
- Refit the **same two** C/20 calibration parameters and freeze them across C/10/C/5. The mean held-out RMSE changed from **129.71** to **129.51 mV** (about **0.20 mV / 0.15%**). Training charge/discharge were **51.62 / 93.87 mV**.

**Decision:** treat as indistinguishable at the available figure-digitisation accuracy, **not** a physically justified improvement or evidence that the substitute `D_s` is correct. The transferred value is not a measurement on the Dessantis cell. Reference: [cross-study evidence § Additional parameter-transfer probe](cross_study_evidence.md).

## 4. Li | LPSCl interfacial series resistance — tried, **not selected** (v0.5)

The resistance term is a *lumped* terminal adjustment `ΔV=-J·ASR`; it does **not** directly resolve pressure-dependent SEI/contact kinetics. The grid was evaluated against C/20 with **fixed** v0.3 `j0` and SoC (no joint re-optimisation):

| ASR (Ω cm²) | C/20 charge RMSE (mV) | C/20 discharge RMSE (mV) | C/20 composite objective | Decision |
|---:|---:|---:|---:|---|
| 0 | 52.408 | 95.107 | **0.0060205807** | **Selected within predeclared grid** |
| 0.8 | 52.439 | 95.103 | 0.0060206660 | Not selected |
| 5 | 52.605 | 95.085 | 0.0060214353 | Not selected |
| 50 | 54.377 | 95.110 | 0.0060642131 | Not selected |
| 200 | 60.322 | 98.399 | 0.0066383773 | Not selected |
| 500 | 72.834 | 113.846 | 0.0093160622 | Not selected |

Selection here is by the recorded composite **C/20 objective** (including duration effects), not by any individual RMSE. The **0.8 Ω cm²** trial comes only from an **unmatched lithium microelectrode context** in [Singh et al., 2023](https://doi.org/10.1002/advs.202302521), **not** a prior estimated for this cell. [Narayanan et al., 2022](https://doi.org/10.1038/s41467-022-34855-9) motivate interface variability but supply **no fitted parameter** here. The 5–500 Ω cm² values are deliberately hypothetical stress tests.

**Decision:** selected ASR remains `0` **as a modelling scenario, not as a physical finding that the interface is resistance-free**. With this selected scenario, held-out mean stayed **129.71 mV**. Refer to [v0.5 report](v05_interface_temperature_report.md) for stage-duration discrepancies and the selection protocol.

## 5. Temperature transport, numerical convergence and studies **not ingested**

- **Temperature scenario, not a full-cell fit:** From Dessantis Fig. 2, electrolyte conductivity is `0.160 S/m` at 25°C and `0.430 S/m` at 50°C. A two-point Arrhenius assumption gives `Ea≈31.676 kJ/mol` and `0.2951 S/m` at 40°C (**interpolation**, not an independent observation). No temperature-dependent OCV, charge-transfer current, or independent 25/40°C cell voltage validation was performed.
- **Mesh/time sensitivity, not an independent solver:** At `(nx,nr,dt_s)=(4,6,300),(6,10,150),(8,16,75)`, C/20 charge/discharge RMSEs were `52.41/95.11`, `52.43/95.05`, `52.45/95.00` mV; C/5 values were `81.32/209.05`, `81.30/209.05`, `81.26/209.05` mV. Only those selected metrics are numerically stable; no fully converged field proof.
- **[Puls et al., 2024](https://doi.org/10.1038/s41560-024-01634-3)**: external multi-lab NMC622/LPSCl dataset, but uses **In/InLi** rather than target **Li metal**; **screened, not ingested/fitted**, requires separate anode protocol.
- **[Schomburg et al., 2025](https://doi.org/10.5281/zenodo.15688067)**: NMC622 OCP reference files are described at Zenodo; the original MAT download was **not available to the execution environment** and data were **not ingested/fitted**.
- **[Sulzer et al., 2021](https://doi.org/10.5334/jors.309)**: PyBaMM is an *intended independent numerical benchmark*, **not a successful validation run**. The earlier environment could not install it. [Issue #2](https://github.com/theerayutbo/SOLiD-PINN/issues/2) remains open.

## Sources, rights and reproducibility

| Citation key | Evidence actually used | Source |
|---|---|---|
| `Dessantis2024` | target cell, source constants, **locally digitised** Figs. 4–5 | [DOI](https://doi.org/10.1016/j.ceja.2024.100610) |
| `IMOTHEP2023` | external OCV **equation**, NMC622 `D_s`; no source raw cell traces | [D4.9 PDF](https://www.imothep-project.eu/files/d4-9-final-battery-model-documentation.pdf) |
| `Singh2023` | *contextual* 0.8 Ω cm² microelectrode scale; not transferred prior | [DOI](https://doi.org/10.1002/advs.202302521) |
| `Narayanan2022` | qualitative EIS/interface motivation only | [DOI](https://doi.org/10.1038/s41467-022-34855-9) |
| `Puls2024` / `Schomburg2025` | screened candidate data, **not ingested or fitted** | [Puls DOI](https://doi.org/10.1038/s41560-024-01634-3) / [Zenodo DOI](https://doi.org/10.5281/zenodo.15688067) |
| `Sulzer2021` | framework/method reference, not an executed PyBaMM comparison | [DOI](https://doi.org/10.5334/jors.309) |

BibTeX: [project citations](../CITATIONS.bib), [additional v0.5 citations](v05_references.bib). Per-source status and licensing notes: [external data registry](external_data_registry.csv). 

**Do not republish digitised source figures/CSVs without rights review.** IMOTHEP's public PDF itself carries a rights notice. Source material and data from distinct chemistries are **not directly interchangeable**. To establish evidence of improvement: obtain author raw traces, define error bars from digitisation, make an independent custom PyBaMM/FEM comparison, then pre-register calibration/hold-out scoring and uncertainty analysis.
