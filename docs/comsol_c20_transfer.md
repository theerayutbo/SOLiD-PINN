# COMSOL collaborator model — parameter transfer and C/20 comparison

2026-11-24. This is an **approximate open-source port of a collaborator-fitted COMSOL model**, not a new calibration, independent experimental validation, or a result at C/10 or C/5. Keep the prior reduced-model benchmark unchanged. COMSOL 6.3.0.290 model settings were read offline from the supplied MPH archive's dmodel.xml; COMSOL itself was not rerun.

## Inputs and provenance

The user supplied the following files privately. Exact filenames and SHA-256 hashes identify the run; original model archive and interpolation/voltage arrays are **not redistributed** here. The source and licensing of the collaborator's OCV, D(theta) and reference curves have not been independently confirmed. The two OCV CSVs exactly match the saved active Uch (111 rows) and Udis (117 rows) interpolation tables.

| File | SHA-256 |
|---|---|
| Part2_fitting_R_C20.zip | 5da5d5717cea7ef70b159fda1f644708dc7fef6ad304fa61689717a6edb8cb2f |
| V_vs_t_C20_sim.txt | da1b565c85ef6cfb3224ec6c4d997a0286f34bf48307ced5d4408b58ff595593 |
| Ref_data_at_C20.csv | 4b9e0f2688a8db78285f8b7b5ad67db4c28f0479196c2f1c5b3bcdf46a5b4c33 |
| OCV_NMC622_SOC.csv | 61951e4e9187af2899a5259002d4b17e80740407791b1bf55b6060cc76404bd9 |
| OCV_NMC622_SOD.csv | e59daa6cae54a114b5d16ca3abf65df5f7c7a3cab66e76e045d949a487981089 |

## Active settings

Single-ion conductor. Active fraction 0.2706, ionic fraction 0.3189, bulk electronic conductivity 0.17 S/m and electronic correction 0.3159^1.5 (effective 0.0301838 S/m). Ionic Bruggeman correction. Reference cathode exchange current 10^0.819 = 6.59173895 A/m2, Li exchange current 100 A/m2. Wch=.5198, Wdch=.538, theta_initial=1-(Wdch-Wch)=.9818. Active area a=3*eps/rp. Applied current based on 165 mAh/g and 5 mg/cm2, not full stoichiometric inventory. Geometric and thermal values match the paper's Table 2. Separate charge/discharge surface-occupancy OCV mappings, D(theta) tables and geometric-current-based R(theta) potential corrections are active. R is embedded in the equilibrium-potential expression, not the film-resistance feature (disabled). No new parameter fitting. These settings include collaborator-fitted values, not necessarily independently measured material constants.

The transfer uses fixed phase fractions, midpoint Galerkin integration of D, linear interpolation/constant extrapolation, symmetric insertion j0=2*j0ref*sqrt(theta*(1-theta)) with endpoint clipping, analytical separator and Li overpotential. It does not claim exact COMSOL internal concentration extrapolation, initialization, volume-change or mesh equivalence. The reported cell_soc is **1-mean(theta)**, not normalized usable SOC. Voltage events only, not the old artificial SOC limits.

## Executed local results

CPU, 4 axial/10 radial P1 elements, adaptive BDF max step 120 s, output grid 30 s plus voltage event. Each discharge inherits its own end-of-charge state. Comparison at stage-local COMSOL samples over common duration, linear interpolation without extrapolation, including t=0. Original trace has 2118 points including paired switch at 17.37115676 h. Charge voltage at switch 4.20004865 V, discharge 4.15117531 V. Final sample 35.25 h at 2.71418916 V; **not a 2.7 V cutoff**. Do not report discharge capacity error from this truncated sample.

| Case | Charge RMSE mV | Discharge RMSE mV |
|---|---:|---:|
| Full transferred settings | 0.097604 | 0.061926 |
| Remove R(theta) | 19.646829 | 29.426683 |
| Constant D=2e-13 m2/s | 1.967484 | 4.996213 |

Full port charge 17.37085645 h, discharge 17.88873931 h. Charge t=0 alone differs by 3.125 mV; excluding t=0 reduces charge RMSE to 0.012784 mV. Coarse 120 s output initially caused 13.84 mV charge RMSE by undersampling the rapid initial transient; corrected output grid 30 s, not a parameter fit. Constant-j0 ablation was interrupted by runtime limits and is not claimed complete. No full convergence or local-field comparison performed.

Reference CSV has 129 samples, 121 within the common absolute cycle time of both simulations. Against those same 121 samples: COMSOL RMSE 28.46684 mV, transferred FEM 28.62750 mV, MAE 10.41238 and 10.45403 mV respectively. No extrapolation, no independent holdout: the reference was provided with a C/20 fitting model. Remaining final reference points excluded because COMSOL export ends early. The numerical match does not establish reproduction of the original paper's experimental capacity errors.

Rerun with authorized input files:
```bash
python scripts/verify_comsol_transfer.py /private/Part2_fitting_R_C20.zip /private/V_vs_t_C20_sim.txt
```
Historical and new numerical summaries are separate. Before adapting the FVM/PyBaMM/PINN to these settings, verify actual COMSOL insertion-kinetics and interpolation defaults, full mesh/time convergence, exact cutoff endpoint, then freeze parameters for independent C/10/C/5 predictions. Keep raw collaborator assets out of the public repository pending explicit redistribution permission.

## References

- Dessantis et al. (2024), DOI https://doi.org/10.1016/j.ceja.2024.100610, Table 2, Fig. 4–5. Published cell target, not source of the collaborator's fitted R or D tables.
- Fuller & Harb (2018), *Electrochemical Engineering*, Ch. 5 and 7, ISBN 9781119004257.
- COMSOL 6.3 [Porous Electrode Reaction](https://doc.comsol.com/6.3/doc/com.comsol.help.battery/battery_ug_electrochem_battery.06.46.html), [Theory for Lithium-Ion Battery Interface](https://doc.comsol.com/6.3/doc/com.comsol.help.battery/battery_ug_electrochem_battery.06.60.html), and [Single-Particle Modeling example](https://doc.comsol.com/6.3/doc/com.comsol.help.models.battery.lib_single_particle/lib_single_particle.html). These motivate the approximate kinetics implementation, not an executed Equation View audit.
