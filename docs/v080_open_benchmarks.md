# v0.8.0 — open benchmark acquisition and qualification

Status: publisher metadata reviewed; actual files not yet acquired/inspected; no experimental benchmark validation. This independent workstream does not overwrite the unresolved v0.7.3 calibration.

## Source-specific roles
- Puls et al., Nature Energy 9, 1310–1320 (2024), DOI https://doi.org/10.1038/s41560-024-01634-3: 21 labs with NMC622/Li6PS5Cl/In-Li. Public files describe processing parameters, cycling summaries and charge-discharge curves. The article reports formation at 0.05C and cycling at 0.1C; these are not a broad multirate sweep. Do not assume the curve workbooks contain original current/time/cycle logs. In/Li electrode potential and kinetics differ from Li metal; no direct voltage pooling with Dessantis. Article CC BY 4.0, inspect file-specific notices. Split by laboratory/cell, not random curve points.
- Petracci, University of Maryland, https://doi.org/10.13016/hiry-dja5, CC0: publisher reports 245 cell records, 167 columns. Use for reporting coverage and physically plausible priors, not time-series training. Verify missingness categories against publisher documentation.
- Fadillah and Coskun, Zenodo https://doi.org/10.5281/zenodo.17816356, CC BY 4.0: two xlsx files, total 76.2 MB; published MD5 in registry. Includes impedance, ASR and cycling data. Li6PS5Cl0.5Br0.5 and surface treatments require separate material/cell definitions. Verify geometry and impedance conditions before converting ASR or conductivity.
- PINNSTRIPES https://github.com/NatLabRockies/PINNSTRIPES: README describes SPM, P2D, SGD/LBFGS, hard initial conditions, PDE/BC/data/regularization losses and Bayesian calibration. Conventional Li-ion methodological benchmark, not ASSB experimental evidence. Reproduce independently before adapting residuals to single-ion solid electrolyte. No upstream code copied.
- Sinzig et al. https://arxiv.org/abs/2408.05771: model-form validity literature, not imported data.
- Dessantis 2024: retain legacy evidence and open model-selection gate. Do not use private collaborator records in a public training bundle.

## Acquisition
Publisher download links in benchmarks/registry.json. Direct UMD download failed in assistant runtime; web retrieval did not expose CSV or workbook bytes. No actual dataset hash, dimensions or completeness claimed. Notebook pins inventory code and runs tests before acquisition. Zenodo publisher MD5 checked before parsing; other computed hashes identify obtained bytes, not publisher-authenticated originals. Declared Excel dimensions are not audited record counts. No upstream raw files committed.

## Admission gates
A: acquisition, attribution, checksum, file/schema inventory.
B: source-specific adapter preserving original units, voltage reference, sign convention, cell/lab/cycle IDs, missingness and pairing; require time/current for time-domain calibration or label capacity-axis-only.
C: material metadata, geometry, boundary conditions; distinguish inferred values from measured values.
D: grouped holdout by cell/lab and chemistry, no random time-point leakage; compare FEM/FVM at matched physical conditions.
E: numerical forward PINN on manufactured/verified synthetic cases can run independently; experimental validation is gated. Do not imply experimental validation, Model C readiness or scientific novelty until supported.

Run the notebook or:
```bash
python -m pip install openpyxl==3.1.5 pytest
python -m pytest -q tests/test_open_benchmark_audit.py
python scripts/audit_open_benchmarks.py --cache /private/benchmarks --out /private/inventory.json --download --source umd --source puls2024 --source liopa
```
