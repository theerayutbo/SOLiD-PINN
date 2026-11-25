import numpy as np
from adaptive_coupled import threshold,select,CAL_SEEDS,TEST_SEEDS,profiles,evaluate

def test_rank():
    assert threshold(range(19))==17
    assert np.isinf(threshold([1,2]))

def test_gate():
    s={'calibrated':1.,'linear':.95,'rbf':.90}
    assert select(s,.11)[0]=='calibrated' and select(s,.09)[0]=='rbf'

def test_disjoint():
    assert not set(CAL_SEEDS)&set(TEST_SEEDS)
    j=profiles();assert set(j)=={'train','val','test','extra'}
    assert not np.array_equal(j['test'],j['val'])

def test_smoke():
    # Same small mesh tests the full selection/diagnostics path, not mesh convergence.
    r=evaluate(999,'weak_rest',1.,False,(4,6,1),(4,6,1))
    assert r['truth_gate_passed'] and r['fit_gate_passed'] and len(r['models'])==3
    for m in r['models'].values():assert np.isfinite(m['test_reaction_density_rmse'])
