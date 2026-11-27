# v0.10.0 — Independent ASSB physics foundation (stage 1)

## Decision and evidence separation
Preserve v0.9.0e as a synthetic AI-methodology baseline (merge 00c8cadadb3b5b700156a5653c631b64019059b8). Start with literature-derived equations rather than fitting Dessantis. This is an initial canonical isothermal electrochemical model, not an exhaustive ASSB theory or a validated material model. No private collaborator data, fitted OCV or paper traces are used. Do not claim capacity fade from a model with no ageing state.

## Source registry
- Wolff, Röder & Krewer, Electrochimica Acta 284 (2018) 639–646, [single-ion P2D model](https://www.sciencedirect.com/science/article/pii/S001346861831630X). Abstract/bibliography inspected; full equation-by-equation audit still pending (publisher full text fetch failed).
- Mykhaylov et al., JMPS 123 (2019) 207–221, [elementary Li-metal/single-ion/composite cathode model](https://www.sciencedirect.com/science/article/abs/pii/S0022509618307002). Abstract and model scope inspected; elementary model not assumed identical to P2D.
- [COMSOL 6.4 single-ion conducting solid electrolyte example](https://doc.comsol.com/6.4/doc/comsol.help.models.battery.li_battery_solid_electrolyte/li_battery_solid_electrolyte.html), Model Definition: fixed counterions + electroneutrality, electrolyte potential only, Ohmic charge transport, spherical Fick diffusion and BV. Example is graphite/LCO, not Li-metal/NMC; independent verification implementation pending.
- [Practical identifiability of electrochemical P2D models](https://doi.org/10.1007/s10800-021-01579-5), ordinary Li-ion study, parameter variation and EIS sections: multiple C-rate curves insufficient for some parameter combinations. Transfer methodology, not its parameter values or conclusions about a specific ASSB.
- Dessantis 2024 [DOI](https://doi.org/10.1016/j.ceja.2024.100610), reserved as first experimental benchmark. Table 1 rate and chronological history confounded; Fig. 5 calibration C/20, C/10 and C/5 held out, Table 3 capacity error <3.5%. C/2 not validation. Table 2 phase fraction ambiguity remains.

## Canonical equation registry (our sign convention and derivation)
Coordinate x=0 at separator/cathode, x=L at collector; r from particle centre to R. Positive J = discharge, positive j = insertion (A/m2 of active surface).
|ID|Equation / constraint|Units / scope|
|---|---|---|
|E01|i_e=-kappa_eff grad(phi_e); i_s=-sigma_eff grad(phi_s)|A/m2 geometric, V, S/m; isotropic constant effective coefficients|
|E02|di_e/dx=-a_s j; di_s/dx=+a_s j; i_e+i_s=J|A/m3; a_s=3 eps_active/R (m^-1), monodisperse spheres|
|E03|dc_s/dt=(1/r^2) d/dr(r^2 D_s dc_s/dr)|mol/m3/s, constant D_s (m2/s) initially|
|E04|D_s dc_s/dr at R = j/F; dc_s/dr at r=0 = 0|insertion increases total particle Li; mol/m2/s|
|E05|j=2 j0 sinh[F(U(c_s(R)/cmax)-(phi_s-phi_e))/(2RT)]|symmetric BV; j0 positive constant illustrative; no film or mechanics|
|E06|separator current J; potential drop J L_sep/kappa_sep; Li boundary potential drop 2RT/F asinh(J/(2j0_Li))|Li metal infinite reservoir, potential reference metal=0; ignores finite Li inventory and space charge|
|E07|i_e(0)=J, i_s(0)=0, i_e(L)=0, i_s(L)=J|ionic/electronic blocking as appropriate; potential/current continuity at separator junction, gauge at Li metal|
|E08|V=phi_s(L) relative Li metal; stop first voltage or occupancy event|ideal collector; no CV stage, thermal evolution or parasitic current|
|E09|m_active=rho_active eps_active A L; Q_lattice=F cmax/(3600 rho_active) Ah/kg = mAh/g|independent geometry/density; usable window not set by observed capacity|
|E10|Q_specific=integral(abs(I) dt)/(3.6 m_active[g]); I=J A; I applied by q_nominal convention|mAh/g; q_nominal sets current, not lattice inventory; event duration predicted|
|E11|theta=c_s/cmax in [0,1]; integral of active inventory change per area = J t (C/m2)|sampled bounds and mass conservation; charge/discharge starts explicitly defined|
These are a proposed canonical reduced-physics equation set under assumptions, not a claim that all ASSB equations have been reviewed. Need independently justify concentration-dependent D, j0 and U, contact area, homogenization laws, finite reservoir, interface films, pressure, temperature and degradation before extension. No electrolyte concentration PDE in this specific fixed-counterion/electroneutral limit.

## Parameter register and audit of existing implementation
All Params defaults in scripts/canonical_fv.py are synthetic, not material measurements: geometry 60/150/6 um cathode/separator/radius, area 1 cm2; phase fractions .35/.40/.20/.05 active/ionic/electronic/void; density 4800 kg/m3; cmax 45000 mol/m3, D=5e-15 m2/s, effective kcat=.004, scat=.08, bulk ksep=.08 S/m, j0=.5 and jli=10 A/m2, T=298.15 K, linear illustrative OCV U=4.4-1.9 theta, cutoffs 2.8/4.15 V, qnom=150 mAh/g. Independent initial theta .80 charge/.15 discharge; separate stages, not sequential cycle or CE. Q can exceed qnom because qnom is current convention, not capacity limit. Phase fractions do not determine effective conductivities in this synthetic test; measure or specify a separate homogenization rule in material model. F and R physical constants. No rate-specific parameters or fitted windows.
Existing src/solid_pinn/parameters.py infers active fraction from nominal capacity assuming full inventory and assumes ionic volume fraction from mass fraction; distinguish these from independently measured geometry. Existing numerical.py uses outer shell average as surface, artificial mean SOC cutoff and frozen flux implicit step; require matched surface reconstruction and actual event definitions before comparison. Earlier docs/v061_physics_audit.md already identified phase-fraction and stoichiometry gaps. docs/comsol_multirate_holdout.md reports frozen FEM vs supplied COMSOL <1 mV on four high-rate stages, but COMSOL exceeds reference-derived discharge capacity by 17.40% C/10 and 44.45% C/5 (conditional durations/current conventions); not an experimental validation. Preserve previous outcomes and private data.

## Executed local stage 1
scripts/canonical_fv.py uses conservative spherical shell volumes, outer-shell centroid extrapolation, axial resistor elimination including half cells, nonlinear inverse BV with total-current constraint, BDF with voltage/occupancy events. All 12 independent stages reached voltage cutoff. Four local tests passed. NumPy 2.3.5, SciPy 1.17.0. Coarse 4x12 max step 300s; fine 8x24 max step 150s. rtol=1e-7, atol=1e-9. Common-time linear interpolation of 101 reported samples (not a continuous maximum). Maximum sampled voltage delta .552402 mV, capacity delta .010276%; mass residual 8.26549e-9 C/m2, mixed algebraic residual 1.94511e-13, sampled theta range [.135815,.837869]. Joint refinement only, not independent spatial and temporal verification.
|Rate|Coarse charge|Fine charge|Coarse discharge|Fine discharge|
|---|---:|---:|---:|---:|
|C/20|165.486756|165.490819|171.437743|171.441805|
|C/10|163.026314|163.034439|168.977301|168.985426|
|C/5|158.124847|158.141097|164.075834|164.092084|
mAh/g; not matched to any real cell.
scripts/foundation_sensitivity.py evaluates log D, ksep, kcat, scat, j0, jli, discharge only, 4x12 mesh, 81 fixed physical time samples per rate through 85% nominal event, divided by assumed IID 5mV SD. Central log step .005 and .0025; relative stacked Jacobian difference 2.9321e-6. At .0025:
|Spectrum|C/20 only|C/20+C/10+C/5|
|---|---:|---:|
|s1|17.0101064|76.8816047|
|s2|.8942888|4.7875509|
|s3|.01353674|.38634846|
|s4|.002773109|.08134194|
|s5|2.97254e-7|.008800036|
|s6|8.01848e-12|.000623155|
C/20 ksep and jli are exactly confounded at fixed current because both are time-constant additive drops; smallest singular value is numerical floor, not meaningful condition number. Stacked condition ~1.234e5 remains poor. More samples as well as distinct currents contribute information. This is local synthetic sensitivity, not global identifiability, posterior, inverse fit or confidence interval; mesh sensitivity of Jacobian still pending.

## Next stage gates
1. Full primary-source equation/BC audit with explicit assumptions and material registry. Agree scope before full implementation.
2. Matched analytic, independent FEM/FVM/PyBaMM/COMSOL: independent axial/radial/time refinement, field comparisons, signed charge/mass closure, per-stage voltage events and capacity. Proposed tolerances 1 mV voltage and .5% capacity, predeclared fields/coverage; no matching by time stretching. Add sequential charge/discharge and rest. Stop if physical or numerical gate fails.
3. Parameter inference: fixed material evidence; local scaled SVD, multistart and profile likelihood for remaining groups, mesh/noise stability; designed pulse/rest and independent EIS/transport evidence to break confounding. Abstain or report parameter groups when unresolved. Compare matched-budget single vs multi-rate training and holdout; no forced individual parameter recovery.
4. Only after numerical gate, generate solver data and compare A supervised ML surrogate, B forward PDE PINN, C inverse PINN vs numerical inverse baseline. Same data splits, noise, parameter bounds, held-out rates; prediction, physical residual, runtime and parameter recovery intervals. Hybrid closure later if verified baseline demonstrably inadequate.
5. Experimental Dessantis C/20 calibration, freeze parameters and initial-state protocol, C/10+C/5 independent holdouts. Since historical results have been examined, label reproduction rather than blind confirmation; reserve new independent data for confirmatory validation. Compare voltage on common physical times with coverage and endpoint, Q_charge and Q_discharge, not only RMSE; no per-rate window fitting or counting capacity and duration as independent evidence. Actual current/cycle IDs, OCV map, phase fractions, loading and metadata needed. C/2 stress test separately. Capacity fade: use repeated fixed-rate cycling and independent degradation data; rate-associated cutoff loss is not necessarily permanent loss.
No full PINN training, COMSOL execution, material calibration, or experimental validation yet.
