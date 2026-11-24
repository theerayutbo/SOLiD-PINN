# v0.7.2 — independent paper reproduction audit

The collaborator COMSOL model is itself an attempted reproduction, not the original author model. Treat it as a separate numerical reference. This work keeps the published-model interpretation, collaborator transfer and future enhanced physics distinct.

## Source and dimensional audit

Dessantis et al. (2024), [DOI](https://doi.org/10.1016/j.ceja.2024.100610), Eq. (3) defines epsilon_s as active material volume fraction; Eq. (5) applies a Bruggeman factor to effective conductivities. Table 2 labels epsilon_s=0.131 as porosity. The precise phase-specific fractions and interpretation of the table cannot be reconstructed uniquely from the text. Table 2 gives 2e-13 m2/s constant D, 10 um particle radius, 40 um cathode, 725 um separator, cmax=csini=47664 mol/m3, 0.43 and 0.17 S/m conductivity, 323.15 K. Nominal capacity 165 mAh/g and approximate active loading 5 mg/cm2 are from the experimental section. Exchange currents and exact OCV interpolation arrays are not specified numerically.

Full lattice inventory per gram is F*cmax*L*epsilon_s/(3600*50 g/m2)*1000 mAh/g. At epsilon_s=0.131 it is 133.88073 mAh/g; at inventory-derived 0.16144967 it is 165; at collaborator 0.2706 it is 276.55058. The reference C20 discharge duration implies 148.60725 mAh/g at the stated current/loading convention. With all other quantities fixed, 0.131 cannot supply that capacity even across the full occupancy range. This is a conditional dimensional inconsistency, not proof of a mistake in the paper: loading is approximate, and the meaning of epsilon_s is ambiguous. For example the minimum active fraction for this discharge is 0.14541 if the full lattice is accessible; a narrower window requires more. Do not substitute a measured-capacity-derived per-rate window.

## Executed Model A: constant-D paper-constrained FEM

Standalone P1 Galerkin in x and spherical r, 4 axial and 10 radial elements, BDF max step 120 s, rtol 1e-7, atol 1e-9; output 30 s plus exact voltage or occupancy event. Charge starts theta=1; discharge inherits the terminal charge concentration. Digitized paper Fig. 4 charge/discharge curves (private reconstructions, PCHIP on SOC=1-theta; not author raw data). Both effective electrode conductivities use 0.131^1.5 as an explicitly provisional Eq. (5) interpretation; collector ideal. Constant symmetric BV, cathode j0=6.59173895 and Li j0=100 A/m2 from collaborator settings as assumptions, not reported paper values. No extra R(theta). No new fit; current alone varies between rates. This is a paper-constrained diagnostic, not an exact original-model reconstruction.

Comparison to the collaborator reference curves: split at maximum voltage, reset stage time at peak, average duplicates within each stage, evaluate on 1000 equally spaced physical-time points from max(60 s, reference start) to common end, no extrapolation. Reference capacity = 165*observed stage duration/rate denominator; endpoint/cycle equivalence with Fig. 5 remains unconfirmed. Capacity error is signed relative to that reference. All eleven completed stages hit voltage cutoffs; max end-state inventory balance absolute error 3.82e-10 mAh/g (not full mesh convergence or independent experimental validation). The literal case covers 93.07% / 89.81% of the C20 reference charge/discharge duration; remaining reported runs cover 100% by end-time ratio. Exclusion of initial interval is explicit.

| Model A variant | Rate | Charge error % | Discharge error % |
|---|---|---:|---:|
| literal epsilon_s=.131 | C20 | -6.93 | -10.19 |
| literal epsilon_s=.131 | C10 | +7.24 | +6.68 |
| literal epsilon_s=.131 | C5 | +35.88 | +33.06 |
| inventory-derived epsilon_s=.16144967 | C20 | +14.73 | +10.73 |
| inventory-derived epsilon_s=.16144967 | C10 | +32.23 | +31.57 |
| inventory-derived epsilon_s=.16144967 | C5 | +67.64 | not completed |

The execution limit interrupted the inventory-derived C5 discharge and prevented the historical-kinetics variant from running. Eleven stage metrics are retained (the last C5 charge was printed and its prediction file written before the aggregate CSV update). No values imputed for missing stages. All six literal-case errors exceed the magnitude 3.5% reported in the paper. Increasing active inventory alone makes high-rate discrepancy worse. See [metrics](results/v072_paper_reproduction_metrics.csv).

## Model B: collaborator simulation / existing transfer

The existing [multirate transfer](comsol_multirate_holdout.md) stays unchanged. Its COMSOL simulation discharge observations are 147.500, 146.423 and 143.469 mAh/g (sampled endpoints, not exact cutoff), against reference 148.60725,124.7169,99.3201. FEM transfer previously agreed with those simulations within 1 mV; that is not paper reproduction. Compare the two models to the same reference durations; Model A voltage events and Model B sampled endpoints differ. Original paper Table 3 signed discharge errors are -2.5%, -3.1%, -2.6%; the original paper's exact Fig. 5 raw data and cycle identity are not confirmed here.

## Reproduce and next steps

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/paper_reproduction.py /private/input_dir --outdir outputs/v072
```

Input directory contains Ref_data_at_C20.csv, Ref_data_at_C10.csv, Ref_data_at_C5.csv and SOLiD-PINN-OCV-Figure4/ocv_charge_digitized.csv and ocv_discharge_digitized.csv. OCV SHA256 respectively 6f4526609a656ee320634d38975c47ea71b36dec08cbfc761d5e4a4469ef4457 and 0ba51db95aca0d9334854251bd14e80104e6fa4afeab34803a99cc5f5bf65d6c; reference hashes in earlier C20 and multirate audits. Original assets and raw curves not redistributed. The new script was executed locally before upload, but three synthetic tests passed locally (0.40 s, test path adapted), but exact repository CI and mesh refinement are not yet verified.

Prioritize independent active fraction/loading and stoichiometric-window evidence, then constant-D and particle-radius sensitivity at a fixed material inventory and independently specified surface kinetics. Fit only C20 with bounded identifiable parameters; freeze C10/C5, report failures and coverage. Already inspected evaluation curves are retrospective, not fresh blinded holdouts. Model C has not been implemented or calibrated; do not label the new diagnostic as an improved solver. Request original author's data/model settings if available. Issue #2 remains open.
