# v0.7.3 — convergence, C/20 selection and rate sensitivity
Status: planned; no new scientific execution in this work package. Input evidence: [Colab audit](v072_colab_reproduction.md). Preserve v0.7.2 runner, inputs and existing results. Use dedicated branches; no direct main writes; do not upload private curves, checkpoints or fitted interpolation tables.

## Gate A — numerical convergence before physical fitting
- Use historical_kinetics as a fixed provisional C20 diagnostic candidate (eps=0.16144967261842047, phase=0.131, j0=0.0566011934 A/m2), same OCV, loading, D=2e-13 m2/s, radius=10 um, voltage events and charge-to-discharge state handoff. Record exact source/input digests, environment and solver options. Also retain literal and inventory-derived comparisons at baseline.
- Implement explicit nx/nr, max_step, rtol/atol arguments without changing v0.7.2 defaults; tests for unchanged defaults, state shape, manifest invalidation, event accuracy and failed runs. Do not reuse states across meshes.
- Spatial ladder: (4,10), (8,20), (16,40), refine again if needed; separate temporal ladder at converged mesh: max step 120/60/30 s, then tolerance 1e-7/1e-9 vs 1e-8/1e-10. Control output sampling independently, compare on common physical time without extrapolation.
- Proposed numerical targets (not paper standards): successive refinement capacity change <=0.5% per stage, voltage RMSE <=1 mV on shared time interval, cutoff time shift <=0.5%, normalized occupancy within bounds and absolute end-state mass error <=1e-6 mAh/g. Report common-time coverage, termination, wall time and failures. If gate fails, refine or document blockage rather than fit.

## Gate B — C/20 model selection
- Compare both charge and discharge, fixed data convention, voltage RMSE, signed capacity error, cutoff and coverage. Project target abs capacity error <=3.5% on both stages; no candidate currently meets both.
- Obtain independent active fraction/loading and operating-window evidence; check phase interpretation and reference cycle/endpoint association. No rate-specific capacity-derived windows. Document bounded identifiable parameters and objective before any fit; use C20 only. If no defensible selection passes, record failure and do not advance to predictive claims.
- Freeze a manifest with selected configuration, evidence, solver resolution and objective; explicitly distinguish a diagnostic baseline from a validated model.

## Gate C — OFAT (only after Gate B)
- Pre-register physically plausible ranges and units before running; exploratory proposed multipliers 0.5/0.8/1/1.25/2 for positive D, particle radius, cathode j0, ionic and electronic conductivity, subject to physical bounds and independent evidence. One factor at a time, same inventory, current and other parameters; avoid conflating radius with effective area, and report coupled geometry effects explicitly. Analyze stoichiometric window only with independent evidence, same fixed window for all rates.
- Record dimensionless diffusion time R^2/D and kinetic/transport effects; report signed capacity changes, RMSE, coverage, cutoff, mass balance and failures. OFAT is screening, not proof of identifiability. Follow with correlation/profile or local Jacobian analysis before multi-parameter fits.
- Freeze C20 selection before evaluating C10/C5 without refitting. Previously inspected curves are retrospective evaluation, not fresh blinded holdout.

## Agent handoff and acceptance
Claude Code: implement and run convergence driver on authorized local inputs, tests and CI; provide aggregate metrics, manifest, figures and negative outcomes in a separate PR. Grok: independent review of convergence and Colab execution when access works; no duplicated writers. ChatGPT: audit evidence, criteria and reproducibility; review before Gate B/C. Do not start Model C or label results experimentally validated until separately justified. All agents coordinate through GitHub and preserve historical work.
