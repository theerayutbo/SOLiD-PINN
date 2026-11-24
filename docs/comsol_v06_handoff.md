# COMSOL collaborator handoff — corrected v0.6.1 benchmark

The original v0.6 results (0.171 S/m) are historical only. The corrected v0.6.1 uses 0.17 S/m after visual verification of Dessantis Table 2 (superscript 1 is a footnote). Run the current branch's three-solver benchmark or use its successful CI artifact; do not compare against the old CSV. See [physics audit](v061_physics_audit.md). COMSOL remains pending.

## Checkout

```bash
git clone https://github.com/theerayutbo/SOLiD-PINN.git
cd SOLiD-PINN
git switch feat/v0.6.1-first-principles-audit
git pull --ff-only
git switch -c validation/comsol-v061
python -m pip install -e '.[dev]'
```

## Match the model before solving

Use the **reduced single-ion model contract** in [the verification report](v06_independent_verification.md), not an unmodified liquid-electrolyte DFN. The following are the actual benchmark inputs from `src/solid_pinn/parameters.py` and `scripts/verify_pybamm.py`, not a claim that they reproduce all physical constants in Dessantis (2024).

| Input | Value |
|---|---:|
| Geometric area | 2.83e-5 m² |
| Separator thickness | 725 µm |
| Cathode thickness | 40 µm |
| Particle radius | 10 µm |
| Separator ionic conductivity | 0.43 S/m |
| Cathode effective ionic conductivity | 0.0643935128969 S/m |
| Cathode electronic conductivity (as coded) | 0.17 S/m |
| NMC lithium diffusion coefficient | 2e-13 m²/s |
| Maximum lithium concentration | 47664 mol/m³ |
| Temperature | 323.15 K |
| Faraday constant | 96487 C/mol |
| Gas constant | 8.314 J/(mol K) |
| Symmetric BV transfer coefficient | 0.5 |
| Cathode exchange current density | 0.0566011934 A/m² |
| Li metal exchange current density | 20 A/m² |
| Inferred active volume fraction | 0.161449672618 |
| Active surface area per cathode volume | 48434.9017855 m⁻¹ |
| Nominal capacity | 0.000233475000000 Ah |
| Extra series ASR | 0 |

For each C-rate denominator `20,10,5`, use signed I=±Q_nom/rate A (negative charge, positive discharge); J=I/A. Absolute currents are 0.00001167375000, 0.00002334750000, 0.00004669500000 A respectively. Use six **independent uniform-start stages**, not sequential cycles. Charge starts with SoC 0.0770454572; discharge starts with SoC 0.90. Initial solid concentration everywhere is c_max*(1-SoC_initial). Stop charge at first V>=4.2 V or SoC>=0.995; stop discharge at first V<=2.7 V or SoC<=0.005. Time horizon is 1.25*rate hours; report actual cutoff reason and include the event endpoint. Use 30 s output spacing plus endpoint. Reference mesh: 12 axial / 20 radial elements or cells. Record COMSOL mesh and solver tolerances and perform refinement rather than assuming discretisation equivalence.

## OCV input (synthetic only)

Generate the shared **illustrative**, non-experimental OCV table from the repository:

```bash
python - <<'PY'
import numpy as np
import pandas as pd
from solid_pinn.ocv import ocv_v
s = np.linspace(0, 1, 2001)
pd.DataFrame({"soc":s,"charge_v":ocv_v(s,"charge"),"discharge_v":ocv_v(s,"discharge")}).to_csv("ocv_v06_synthetic.csv",index=False)
PY
```

Use stage-specific interpolation of these values with input SoC=clip(1-c_surface/c_max,0,1). The original FEM/FVM use PCHIP; PyBaMM uses dense linear interpolation of the same curve. Document COMSOL interpolation. Do not use digitised experimental OCV, change parameters, or recalibrate for this verification.

## Return results

1. Run [equation_audit_shell.java](../scripts/comsol/equation_audit_shell.java) in the authorized COMSOL Java Shell with the model loaded; check output for unavailable tables. Record COMSOL version and any equation/sign/units differences. The script has not been executed here.
2. Export **all six stages** with columns `time_s,voltage_v,soc,stage,rate,sigma_cathode_s_m`; use stage-local t=0, SoC as a fraction (not percent), lowercase charge/discharge, rate as integer denominator and sigma_cathode_s_m = 0.17 in every row. Include exact event row. Export spatial potentials, reaction current and radial concentration at common physical times if available, with units and coordinates.
3. Save permitted numerical output under `docs/results/comsol/v061_comsol_results.csv`. Add a README in that folder recording COMSOL version, model construction, equations/assumptions, parameter differences, OCV interpolation, mesh/refinement, solver settings, cutoff reason, run date, runtime/hardware and any missing data. Keep proprietary equation exports, copyrighted figures, licensed model files and data without redistribution permission out of the public repo; share privately if authorized.
4. Run the existing conditional FVM comparator (2001 common-time points; pairwise interval may differ from the three-solver common interval) as a preliminary check:
```bash
python scripts/compare_comsol_csv.py docs/results/comsol/v061_comsol_results.csv --out docs/results/comsol/v061_comsol_comparison.csv
git add docs/results/comsol/
git commit -m "results: add matched COMSOL v0.6.1 verification with provenance"
git push -u origin validation/comsol-v061
```
Open a PR **targeting feat/v0.6.1-first-principles-audit** (not main). If the collaborator lacks write access, use a fork with the same PR target. Do not force push. The final four-way comparison must use identical common-time grids and report failed cases.

**Reference:** Dessantis et al. (2024), [DOI](https://doi.org/10.1016/j.ceja.2024.100610); Sulzer et al. (2021), [DOI](https://doi.org/10.5334/jors.309); COMSOL documentation linked in the [verification report](v06_independent_verification.md).
