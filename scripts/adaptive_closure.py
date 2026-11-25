"""Null-calibrated closure activation, synthetic independent seed benchmark."""
import argparse,json,math,platform
from pathlib import Path
import numpy as np
import scipy
from missing_physics import design,simulate,fit,observe,rmse,rates,missing
NOISE=(1.,5.)
CAL_SEEDS=tuple(range(1000,1019))
TEST_SEEDS=tuple(range(2000,2008))
TRUTHS=('null','rest','peak','weak_rest')
METHODS=('calibrated','linear','hybrid_rbf')
LAM=10.
ALPHA=.10

def threshold(scores,alpha=ALPHA):
    s=np.asarray(scores,float)
    if not len(s) or not np.all(np.isfinite(s)) or not 0<alpha<1:raise ValueError('invalid calibration')
    k=math.ceil((len(s)+1)*(1-alpha))
    return max(0.,float(np.sort(s)[k-1])) if k<=len(s) else float('inf')

def select(scores,q):
    best=min(METHODS[1:],key=lambda m:scores[m]);gain=scores['calibrated']-scores[best]
    return (best if gain>q else 'calibrated'),float(gain)

def evaluate(seed,truth,noise,cal=False):
    rng=np.random.default_rng(seed);ptrue=np.r_[rng.uniform(.08,.12),rng.uniform(.55,.85),rng.uniform(.04,.08),.15 if truth=='weak_rest' else 1.]
    law='rest' if truth=='weak_rest' else truth
    js=design();xs={k:simulate(j,'oracle',ptrue,law,True) for k,j in js.items()};vs={k:observe(js[k],x) for k,x in xs.items()}
    y=vs['train']+rng.normal(0,noise,vs['train'].shape);v=vs['val']+rng.normal(0,noise,vs['val'].shape)
    error=max(rmse(simulate(j,'oracle',ptrue,law),xs[k]) for k,j in js.items());assert error<1e-6
    rows={};scores={}
    for m in METHODS:
        p,ok,n=fit(m,'null',js['train'],y,0. if m=='calibrated' else LAM)
        if not ok:raise RuntimeError(f'fit failed {seed} {truth} {noise} {m}')
        scores[m]=float(np.mean((observe(js['val'],simulate(js['val'],m,p,'null'))-v)**2)/noise**2)
        if not cal:
            xp={k:simulate(j,m,p,'null') for k,j in js.items() if k not in ('train','val')};grid=np.linspace(0,4,101);d=rates(m,p,'null',grid)[2]
            row={k+'_rmse_mv':rmse(observe(js[k],x),vs[k]) for k,x in xp.items()}
            row.update(closure_rmse=rmse(d,ptrue[3]*missing(law,grid)),rest_closure=float(d[0]),min_state=float(min(x.min() for x in xp.values())),max_state=float(max(x.max() for x in xp.values())),nfev=n,params=p.tolist())
            assert 0<=row['min_state']<=row['max_state']<=1
            rows[m]=row
    raw,gain=select(scores,0.)
    return dict(seed=seed,truth=truth,noise=noise,validation_scores=scores,gain=gain,raw=raw,reference_error=error,truth_params=ptrue.tolist(),models=rows)

def run():
    calibration=[];test=[];thresholds={}
    for noise in NOISE:
        cal=[evaluate(s,'null',noise,True) for s in CAL_SEEDS];calibration.extend(cal)
        q=threshold([x['gain'] for x in cal]);thresholds[str(noise)]=q
        print('calibrated',noise,q,flush=True)
        for truth in TRUTHS:
            for seed in TEST_SEEDS:
                row=evaluate(seed,truth,noise);row['gated']=select(row['validation_scores'],q)[0];test.append(row)
            print('evaluated',noise,truth,flush=True)
    return dict(scope='synthetic binary closure gate; no experimental validation or unique mechanism identification',environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),protocol=dict(noise=NOISE,cal_seeds=CAL_SEEDS,test_seeds=TEST_SEEDS,truths=TRUTHS,methods=METHODS,lambda_fixed=LAM,alpha=ALPHA,weak_rest_amplitude=.15,base_ranges=[[.08,.12],[.55,.85],[.04,.08]]),thresholds=thresholds,calibration=calibration,test=test)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();Path(a.out).write_text(json.dumps(run(),indent=2,allow_nan=False)+'\n')
