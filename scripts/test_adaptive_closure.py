import numpy as np
from adaptive_closure import threshold,select,CAL_SEEDS,TEST_SEEDS,evaluate

def test_rank():
    assert threshold(range(19))==17
    assert np.isinf(threshold([1,2]))

def test_gate():
    s={'calibrated':1.,'linear':.95,'hybrid_rbf':.9}
    assert select(s,.11)[0]=='calibrated'
    assert select(s,.09)[0]=='hybrid_rbf'

def test_disjoint():
    assert not set(CAL_SEEDS)&set(TEST_SEEDS)

def test_null_fit():
    r=evaluate(999,'null',1.,True)
    assert np.isfinite(r['gain']) and r['reference_error']<1e-6 and r['models']=={}
