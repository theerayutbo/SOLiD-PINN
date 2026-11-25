# Research baseline v0.9.0b

Integration commit: [465611e](https://github.com/theerayutbo/SOLiD-PINN/commit/465611e2ed08aa35aa34a0cd27c562ddeb028ad0), PR #40. Scope v0.8.3–v0.9.0b, with v0.8.0–v0.8.2 dependencies. v0.9.0c and unrelated reproduction drafts are excluded. **Synthetic research milestone, not experimental validation or a completed nonlinear full P2D PINN.**

## Frozen manifest
[Manifest](research_baseline_v090b.json) records source/test Git blob hashes, archived summary SHA-256 digests, and exact replay commands. Run the archive checker and regression tests separately from full computational experiments. The checks verify the committed synthetic artifacts, not the validity of physical assumptions.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install 'torch==2.10.0' --index-url https://download.pytorch.org/whl/cpu
python -m pip install 'numpy==2.3.5' 'scipy==1.17.0' '.[dev]' requests
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python scripts/verify_research_baseline.py
python -m pytest -q scripts/test_inverse_interface.py scripts/test_bayes_interface.py scripts/test_mismatch_benchmark.py scripts/test_dynamic_benchmark.py scripts/test_constrained.py scripts/test_missing_physics.py scripts/test_adaptive_closure.py scripts/test_hybrid_p2d.py scripts/test_mesh_bridge.py scripts/test_publish_colab_uq.py
mkdir -p outputs/baseline
```

Python 3.13 and CPU PyTorch are recommended for the recorded environment. Exact patch/library differences can alter numerical output; archive hashes validate stored bytes, not bitwise equality of independently computed floating-point results. For full replay run the manifest commands from repository root. Keep generated files outside the frozen evidence. Full fits are not rerun by the unit-test workflow.

## Evidence ladder
- v0.8.3–v0.8.9: local numerical/synthetic experiments; v0.8.4 has user-returned Colab aggregate evidence.
- v0.9.0a: 72 fits reproduced on Colab but the historical spatial gate failed. Preserve the failed result.
- v0.9.0b: 216/216 synthetic fits in the returned Colab archive, all expected keys; final adjacent refinement pairs pass 1 mV on all three profiles; maximum archived final delta ~0.2493 mV. Terminal closure, known observation map, no reaction/transport feedback.
- RBF closure improves interpolation for supplied rest/peak missing-physics cases, but worsens null and may lose to linear closure on extrapolation. No universal superiority or unique mechanism claim.
- Independent experimental validation, uncertainty under broader model mismatch and coupled physical closure remain open.

The integration's existing Tests CI passed on Python 3.10, 3.12 and PINN job. A separate research-baseline workflow explicitly collects script-based tests otherwise outside default pytest discovery. Its result must be checked at the actual commit before claiming a new green status. No private measurement data is required for these synthetic tests.

Future research must branch from this baseline, keep evidence immutable, disclose changed equations and protocols, and repeat the relevant tests; do not rewrite the recorded historical hashes. A successor manifest is needed if frozen source files change. See the experiment-specific reports and [Colab v0.9.0b audit](results/colab/v090b_reproduction_audit.md).
