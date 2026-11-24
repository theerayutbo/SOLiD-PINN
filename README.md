# SOLiD-PINN

**Solid-state Lithium Dynamics with Physics-Informed Neural Networks**

Reproducible, open-source **research scaffold** inspired by Dessantis et al.
(2024): *Investigating sulfide-based all solid-state cells performance through
P2D modelling*, Chemical Engineering Journal Advances **18**, 100610.
https://doi.org/10.1016/j.ceja.2024.100610

> [!IMPORTANT]
> **Status: v0.5 feasibility prototype, NOT a verified reproduction of the paper.**
> We transcribed reported physical constants and implemented a reduced P2D
> finite-volume solver plus an actual physics-informed neural network for
> **synthetic single-ion electrolyte inverse conductivity**. Experimental
> charge/discharge traces and numerical OCV tables are not provided in the
> paper. The curves produced by this repository currently use explicitly
> **illustrative OCV data and assumed interface kinetics**; do not compare
> reported errors as if they were experimentally validated.

## Goals

1. Reproduce Li | Li6PS5Cl | NMC622 single-ion all-solid-state half-cell physics.
2. Numerically solve composite-cathode axial charge conservation coupled to
   spherical NMC lithium diffusion, lithium boundary BV kinetics and cycling.
3. Develop physics-informed learning for electrolyte conductivity identification.
4. Recover the article's Figure 5 voltage profiles and Table 3 capacity errors
   **after obtaining trace/OCV data and calibrating missing parameters**.
5. Benchmark speed, identifiability, physics compliance and held-out C-rate prediction.

## Quick start

Python 3.10+:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,pinn]'
pytest -q
solid-pinn simulate --rates 20 10 5 --outdir outputs
solid-pinn pinn-demo --epochs 900
```

The first command generates `outputs/synthetic_C_*.csv`, `summary.csv` and
`synthetic_voltage_curves.png`. These are **prototype predictions only**.

After obtaining real OCV points, supply **both** branches with headers
`soc,voltage_v`:

```bash
solid-pinn simulate --charge-ocv data/experimental/ocv_charge.csv \
  --discharge-ocv data/experimental/ocv_discharge.csv
```

This replaces the illustrative OCV, but still requires calibration of unknown
interface exchange currents/volume fractions and validation with trace data.

The PINN demo synthesises `phi(x) = -J*x/kappa` with true
`kappa=0.43 S/m`, and attempts to infer conductivity with sparse data,
PDE residual and flux boundary loss. No experimental values are used.

## Architecture

```text
src/solid_pinn/
    parameters.py    Paper constants vs explicit assumptions
    ocv.py           Illustrative OCV placeholders: NOT digitised data
    numerical.py     Reduced 1D-x + 1D-r P2D finite-volume solver
    pinn.py          PyTorch PINN inverse conductivity subproblem
    validation.py    Capacity and voltage comparison metrics
    cli.py           Experiment runner / diagnostic plot

tests/               Conservation, parameters, metrics, smoke, PINN inverse
.github/workflows/   CI tests in multiple Python versions

docs/                Reproduction protocol and evidence gaps
```

## v0.2 numerical verification

The branch `fix/v0.2-physics-validation` improves the feasibility prototype:

- The reduced P2D simulator bisects a time step to locate the first voltage or
  SoC cutoff, rather than always rounding cycle capacity to the next step.
- Independent *analytical* spherical-diffusion eigenmode tests exercise spatial
  and temporal convergence of the radial finite-volume operator.
- The synthetic SSE inverse PINN now generates dimensional voltages using
  applied current density, separator thickness and conductivity before
  normalising them for stable training. A proportionally scaled relative-noise
  model is invariant to J and L after normalisation, as physics predicts.
- PINN tests check dimensional voltage scaling and reject invalid noise.

**Limits:** cutoff event interpolation does not eliminate finite-time-step
integration error. The spherical analytical benchmark is **not** an independent
full-P2D solver check. PyBaMM/COMSOL-equivalent P2D cross-validation, measured
OCV traces and research-grade uncertainty quantification remain outstanding.

See [verification guidance](docs/verification.md).

## Research design

| Module | Target | Current status |
|--|--|--|
| Li metal | Boundary potential / kinetics | Simplified BV boundary |
| Li6PS5Cl | Single-ion transport / Ohm's law | Implemented |
| NMC622 | Radial Fick + volume-averaged electrochemistry | Finite-volume, simplified |
| Galvanostatic | C/20, C/10, C/5 | Implemented with illustrative OCV |
| PINN | SSE conductivity inversion | Implemented, synthetic data only |
| Full P2D PINN | Coupled potentials + diffusion + BV | Roadmap |
| PyBaMM benchmark | Independent scientific numerical cross-check | Roadmap |
| Dessantis Fig. 5 validation | Experimental measured curves | **BLOCKED: data unavailable** |

The main source-based commitments and unresolved discrepancies are
recorded in [`docs/reproduction_protocol.md`](docs/reproduction_protocol.md).

## Data and scientific integrity

The source paper says, "Data will be made available on request." No source
PDF, figures, copyrighted content or reconstructed measurements are bundled.
See [`data/README.md`](data/README.md) before publishing any claims.

## License
MIT for original project code. The source article remains under its own
CC BY-NC-ND licence; no paper figures or text are re-licensed here.
## v0.4 — independent OCV cross-study ablation

A predeclared sensitivity experiment compares Dessantis Figure 4-derived
charge/discharge pseudo-OCV with the independent AIT/KIT NMC622
single-valued OCV equation in [IMOTHEP D4.9 Table 3](https://www.imothep-project.eu/files/d4-9-final-battery-model-documentation.pdf).
Weights 0%, 25% and 50% are **illustrative blends, not physically mixed
electrode parameters**. Fitting uses only C/20, while C/10 and C/5 are
held out. Under a four-curve mean held-out voltage-RMSE score, the original
source OCV remains best: 129.71 mV (baseline), 131.95 mV (25%), 148.34 mV
(50%); curves are digitised **not experimental raw data**. These figures
do **not** establish scientific validation, transferability or paper
reproduction. See [cross-study report](docs/cross_study_evidence.md),
[citation file](CITATIONS.bib) and
[source data registry](docs/external_data_registry.csv).

Run on user-authorized input CSVs:
```bash
python scripts/compare_cross_study_ocv.py --charge-ocv /private/charge.csv \
 --discharge-ocv /private/discharge.csv --c20 /private/c20.csv \
 --c10 /private/c10.csv --c5 /private/c5.csv
```

A separate exploratory sensitivity test of NMC622 diffusion using IMOTHEP D4.9 Table 2 is documented in [v0.4 evidence](docs/cross_study_evidence.md); its held-out RMSE change (~0.15%) is too small to claim an improvement.

## Auditable calibration outcomes (v0.3–v0.5)

All evaluated parameter alternatives, including **rejected** and **inconclusive**
trials, are documented in the [calibration experiment ledger](docs/calibration_experiment_ledger.md)
and [machine-readable trial metrics](docs/calibration_trial_metrics.csv).
Source references include the original Dessantis paper, IMOTHEP D4.9,
Singh/Narayanan interface studies and screened external datasets, with
BibTeX in [CITATIONS.bib](CITATIONS.bib) and
[additional v0.5 references](docs/v05_references.bib).

Under the recorded four-stage held-out RMSE metric (C/10 and C/5), the
Dessantis-only OCV baseline remains **129.71 mV**. Using an unmatched IMOTHEP
OCV at 25% or 50% gave **131.95 mV** and **148.34 mV**, respectively,
and was **not adopted**. Substituting IMOTHEP solid diffusivity yielded
**129.51 mV**, only ~0.20 mV different and **inconclusive**. Optional interface
ASR candidates up to 500 Ω cm² did not improve the predeclared C/20
selection objective. The chosen grid scenario remained 0 Ω cm²; this
**does not imply the physical interface resistance is zero**.

All reported scores are from **locally digitised, non-redistributed figure
traces**, NOT authors' experimental raw data or independently validated
full-P2D predictions. A good training fit is **not evidence of transfer**.

## v0.6 independent verification (historical: 0.171 S/m)

The matched PyBaMM/FEM/FVM benchmark successfully ran in [GitHub Actions run 45448266696](https://github.com/theerayutbo/SOLiD-PINN/actions/runs/45448266696). Six independent uniform-start scenarios use the same illustrative OCV and reduced-model parameters. PyBaMM vs FEM voltage RMSE is below 0.074 mV in all six; overall 16/18 pairwise voltage RMSE checks pass the 1 mV target and 18/18 capacity checks pass the 0.5% target. FVM comparisons at C/5 discharge exceed the voltage target. This is numerical verification, not experimental validation.

- [Verification report](docs/v06_independent_verification.md)
- [Executed three-solver results CSV](docs/results/v06_three_solver_matched.csv)
- [COMSOL collaborator handoff](docs/comsol_v06_handoff.md) — exact benchmark inputs, equation audit and result export instructions.

COMSOL execution, full spatial-field comparisons and mesh convergence remain outstanding. Issue #2 remains open.

## v0.6.1 corrected benchmark

Dessantis Table 2 reports **0.17 S/m**, not 0.171 (superscript 1 is a footnote). All new runs use 0.17 S/m by default. Historical calibration and v0.6 CSVs remain immutable; rerun them only at their recorded revision. See [first-principles audit](docs/v061_physics_audit.md) and [corrected COMSOL handoff](docs/comsol_v06_handoff.md). Corrected three-solver results must come from the new CI run, not the historical CSV. Phase fractions and usable stoichiometry remain unverified.

## COMSOL C/20 simulation reference (unmatched sequential cycle)

A collaborator voltage-only export has been analyzed without redistributing the raw data. See [COMSOL audit](docs/comsol_c20_reference_audit.md), [exploratory metrics](docs/results/comsol_c20_exploratory_metrics.csv), and [corrected three-solver benchmark](docs/results/v061_three_solver_matched.csv). These are separate protocols; neither constitutes experimental validation. Full COMSOL parameter, current, OCV and equation metadata remain required.

## Collaborator COMSOL C/20 parameter transfer

The separate approximate FEM port reads an authorized local COMSOL MPH/ZIP (no COMSOL runtime required to read settings), applies the saved stoichiometric windows, active/ionic fractions, concentration-dependent diffusion and resistance. It does not replace the previous numerical reference model. Local C/20 transfer RMSE vs COMSOL: 0.098 mV charge and 0.062 mV discharge without refitting. This is a comparison to an already fitted simulation, not independent experimental validation. See [transfer report](docs/comsol_c20_transfer.md) and [negative ablations](docs/results/comsol_transfer_c20_summary.csv). Original collaborator files and interpolation arrays are not redistributed. C/10 and C/5 holdouts and field/mesh verification remain open.
