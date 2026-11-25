import numpy as np
import torch
from mismatch_benchmark import TRAIN,TEST,TIMES,true_rate,truth,rk4,observe,numerical,Hybrid

def test_rk4_matches_reference():
    a=np.r_[TRAIN,TEST]; x=rk4(a,true_rate); assert np.max(np.abs(x-truth(a)))<1e-6
    assert np.all((x>=0)&(x<=1))

def test_oracle_recovery():
    y=observe(TIMES[:30,None],TRAIN,truth(TRAIN)[:30]);rate,p=numerical('oracle',y)
    np.testing.assert_allclose(p,[.1,.7],rtol=1e-5)
    np.testing.assert_allclose(rate(TEST),true_rate(TEST),rtol=1e-5)

def test_neural_initial_and_bounds():
    m=Hybrid().double();j=torch.tensor([[.25],[4.]],dtype=torch.float64);t=torch.zeros_like(j)
    assert torch.all(m.state(t,j)==0);assert torch.all(m.rate(j)>0)
    assert torch.all((m.state(t+50,j)>0)&(m.state(t+50,j)<1))

def test_disjoint_currents():
    assert not np.intersect1d(TRAIN,TEST).size
