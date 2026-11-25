import numpy as np
from coupled_bridge import simulate as original,healthy,profile
from robust_mechanisms import whiten,noise,decision,evaluate,truth_predict,CAL,NULL,ALT,METHODS
from robust_solver import simulate

def test_original():
    j=profile('test');p=[.35,.7,1.];a,_,_=original(j,'oracle',p,'rest',(4,6,1),True);b,c,_=simulate(j,'oracle',p,'rest',(4,6,1),True);np.testing.assert_array_equal(a,b);assert healthy(c)

def test_noise():
    rng=np.random.default_rng(1);z=noise(rng,(2000,10),.8);w=whiten(z,.8);assert abs(w.std()-.005)<.0002;assert abs(np.corrcoef(w[:-1].ravel(),w[1:].ravel())[0,1])<.03

def test_truths():
    j=profile('test');p=[.35,.7,1.];v,_,f=truth_predict(j,'null',p,(4,6,1));
    for t,z in [('diffusion',.65),('kinetic',1.25),('series',.12)]:
        u,c,g=truth_predict(j,t,[.35,.7,z],(4,6,1));assert healthy(c) and np.max(abs(u-v))>1e-5
        if t=='series':np.testing.assert_array_equal(f,g)
        else:assert np.max(abs(f-g))>1e-8

def test_gate():
    scores={m:1. for m in METHODS};scores['series']=.8;assert decision(scores,.1)[0]=='series';assert decision(scores,.3)[0]=='calibrated';assert not set(CAL)&set(NULL+ALT) and not set(NULL)&set(ALT)

def test_smoke():
    r=evaluate(999,'diffusion',.8,False,(4,6,1),(4,6,1));assert r['truth_gate_passed'] and r['fit_gate_passed'] and len(r['models'])==6
    assert all(np.isfinite(m['test_reaction_density_rmse']) for m in r['models'].values())
