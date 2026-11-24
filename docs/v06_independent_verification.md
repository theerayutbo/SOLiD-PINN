# v0.6 — independent numerical and COMSOL equation verification

Status: partial verification. No new experimental calibration, no new claim of Dessantis reproduction. The FEM was executed locally on synthetic illustrative OCV. PyBaMM is a separate implementation submitted to CI; check the actual workflow and artifact before calling it verified. COMSOL extraction is a read-only script for an authorized licensed installation, not an executed comparison.

## Reference model contract

All solvers must use the same sign convention: J=I/A positive for discharge, j positive for insertion into the cathode. In the cathode: i_e=-kappa_eff*d(phi_e)/dx, i_s=-sigma*d(phi_s)/dx; d(i_e)/dx=-a*j, d(i_s)/dx=a*j. j=-2*j0*sinh(F*(phi_s-phi_e-U)/(2*R*T)). At the left of the cathode i_e=J, i_s=0; at the right i_e=0, i_s=J. Separator is analytically reduced to phi_e(0)=-asinh(J/(2*j0_Li))/beta-J*L_sep/kappa_sep with beta=F/(2*R*T); no electrolyte concentration equation. The particles obey spherical Fick diffusion with dc/dr=0 at r=0 and dc/dr=j/(F*D) at r=R_p. Initial concentration, stage-specific OCV, voltage/SoC cutoffs, and material parameters must be aligned before comparison. Default ASR is zero. These are the existing *reduced* model assumptions; they are not yet demonstrated to be exactly the original paper's full COMSOL model.

## A. Executed independent FEM benchmark

`reference_fem.py` independently assembles piecewise-linear Galerkin axial and spherical radial mass/stiffness matrices, inverts the symmetric BV law, and integrates by adaptive BDF. It does not call the original FVM discretisation. It shares parameter values and OCV only. `scripts/verify_fem.py` compares full sequential charge/discharge cycles; C/20, C/10, C/5; j0=0.0566011934 A/m2, starting SoC=0.0770454572, illustrative OCV, 50 C. The discharge stages inherit the end-of-charge state for each solver separately. Numerical agreement is not experimental accuracy.

| C-rate/stage | Voltage RMSE at 150 s sampling (mV) | Voltage RMSE at 30 s sampling (mV) | Absolute capacity difference at 30 s (%) |
|---|---:|---:|---:|
| C/20 charge | 0.03667 | 0.03663 | 0.00614 |
| C/20 discharge | 0.50444 | 0.50455 | 0.00568 |
| C/10 charge | 0.06641 | 0.06639 | 0.01252 |
| C/10 discharge | 1.03593 | 1.02862 | 0.01156 |
| C/5 charge | 0.11928 | 0.11955 | 0.02569 |
| C/5 discharge | 3.65705 | 2.12781 | 0.02368 |

FEM nx=6,nr=10 (elements), FVM nx=12,nr=20 (cells). The two runs vary maximum BDF step/output sampling and fixed FVM step; no independent full mesh-convergence claim. Common-stage interval voltage RMSE is evaluated on 501 uniformly spaced times. Capacity difference is signed relative to FEM, based on stage durations at identical applied current; absolute values above. Max SOC-balance discrepancy relative to nominal capacity was below 3e-10% for FEM and 7e-11% for FVM in the 30 s run. Integrated current balance was below 5e-14% in FEM at sampled states and FVM at final state. These are numerical residuals under the model's inferred nominal-capacity convention, not independent experimental mass measurements. FVM current balance is only checked at the final state in this driver. Fields at respective cutoff times are not a same-time comparison. Local radial concentration agreement and full field convergence still need quantification.

**Gates:** voltage <1 mV: 4/6 passed; capacity <0.5%: 6/6 passed; stated mass/current checks <0.01%: 6/6 passed. C/10 and C/5 discharge fail the voltage target; keep the negative results. These tolerances are project targets, not published standards. Use `python scripts/verify_fem.py --dt 30` to rerun. Coarse and fine CSV summaries are included; no digitised figure traces are committed.

## B. PyBaMM

`reference_pybamm.py` defines a custom symbolic single-ion reduced P2D model using BaseModel, spherical particle auxiliary domain, finite-volume discretisation and IDAKLU. It is not the default liquid-electrolyte DFN. The analytic separator boundary is shared as a mathematical assumption, and OCV is approximated on a dense linear interpolation grid. PyBaMM uses surface reconstruction, which differs from the old FVM's outer-shell concentration approximation; quantify that difference rather than silently forcing the outputs to match.

`scripts/verify_pybamm.py` tests six **independent uniform-start stages** at SoC 0.0770454572 (charge) or 0.90 (discharge), not the sequential FEM cycles above. Its results must not be pooled as if the initial discharge profiles were identical. Use the same uniform start for COMSOL. The driver reports common-time voltage RMSE, capacity, SOC balance and integrated current balance. Full field comparisons and mesh refinement remain to be implemented. Run on Python 3.12, `pip install -e '.[dev]' pybamm==25.10.2`, then `python scripts/verify_pybamm.py`. Dedicated GitHub Actions workflow uploads CSV when it actually succeeds. Local package installation was unavailable; no PyBaMM numbers claimed here.

## C. COMSOL (licensed model required)

Official documentation: [single-ion conductor interface](https://doc.comsol.com/6.4/doc/com.comsol.help.battery/battery_ug_electrochem_battery.06.02.html), [application example](https://www.comsol.com/model/lithium-ion-battery-with-single-ion-conducting-solid-electrolyte-71471) (not the target cell), [Equation View](https://www.comsol.com/support/learning-center/article/viewing-and-accessing-the-equations-and-variables-for-physics-feature-nodes-30761), [Java API FeatureInfo](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/api/com/comsol/model/physics/FeatureInfo.html), [physics API](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_api_general.47.51.html).

1. Open a user-authorized .mph model in a licensed COMSOL installation, record COMSOL version and study; enable Equation View and update the model if necessary.
2. Paste `scripts/comsol/equation_audit_shell.java` into Java Shell. It reads recursive Expression, Weak, Constraint, Shape tables via featureInfo("info").getInfoTable(...). It does not solve or modify the model. Review unavailable tables and report omissions. It has not been tested in COMSOL here.
3. Compare each contribution with the contract above, including actual phase fractions and conductivity scaling, exchange-current definitions, particle geometry/surface convention, signs, units, and current collector treatment. The example application model's geometry/chemistry must not be mistaken for Dessantis.
4. Construct matched scenarios with the same parameters, illustrative OCV, and uniform initial SoC as PyBaMM benchmark, solve at C/20, C/10, C/5 in both directions. Export terminal voltage and volume-weighted SoC with stage-local seconds, canonical CSV columns `time_s,voltage_v,soc,stage,rate`; rate is denominator 20/10/5. Also export x/r fields for later comparison, plus metadata including units, cutoff reason, mesh and time integration settings. The comparator cannot itself establish that the exported model or initial fields are matched.
5. Run `python scripts/compare_comsol_csv.py /private/comsol_results.csv`. It reports conditional numerical metrics; the script is not proof that the supplied data came from COMSOL or a matched model. No COMSOL execution here (no license/runtime/original .mph). Keep any proprietary equation export or source figures private unless authorized.

## References and next gates

- Dessantis et al. (2024), DOI [10.1016/j.ceja.2024.100610](https://doi.org/10.1016/j.ceja.2024.100610), governing equations, reported constants and experiment protocol; see [CITATIONS.bib](../CITATIONS.bib).
- Sulzer et al. (2021), DOI [10.5334/jors.309](https://doi.org/10.5334/jors.309), PyBaMM framework; [custom half-cell documentation](https://docs.pybamm.org/en/latest/source/examples/notebooks/creating_models/5-half-cell-model.html), modified sign and boundary conventions for this project. See [v05 references](v05_references.bib).
- COMSOL official references above, not data sources or evidence of execution.

Issue #2 remains open: complete independent PyBaMM run, acquire matched COMSOL model/export, verify concentrations and spatial fields at identical physical time, resolve discharge discrepancy, then validate against author-supplied experimental data. Retain the historical calibration ledger unchanged.
