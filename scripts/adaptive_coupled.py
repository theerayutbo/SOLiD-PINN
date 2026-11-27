"""Prospective null-calibrated selection for the coupled reduced x-r model."""
import argparse,json,math,platform,time
from pathlib import Path
import numpy as np
import scipy
from coupled_bridge import simulate,fit,healthy,verify,FIT,REF,profile,DT,rmse,rates,missing
METHODS=('calibrated','linear','rbf')
TRUTHS=('null','rest','peak','weak_rest')
NOISE=(1.,5.); CAL_SEEDS=tuple(range(1000,1019)); TEST_SEEDS=tuple(range(2000,2008)); ALPHA=.1

def threshold(scores,alpha=ALPHA):
    a=np.asarray(scores,float)
    if not len(a) or not np.isfinite(a).all() or not 0<alpha<1:raise ValueError('invalid calibration')
    k=math.ceil((len(a)+1)*(1-alpha))
    return max(0.,float(np.sort(a)[k-1])) if k<=len(a) else float('inf')

def select(scores,q):
    best=min(METHODS[1:],key=scores.get);gain=scores['calibrated']-scores[best]
    return (best if gain>q else 'calibrated'),float(gain)

def profiles():
    j={k:profile(k) for k in ('train','test','extra')}
    val=np.repeat(np.array([[.4,-1.1,0,2.4,-.9,-2.4],[-2.4,.9,1.1,0,-.4,2.4]],float).T,8,axis=0)
    j['val']=np.r_[val,val[-1:]];return j

def evaluate(seed,truth,noise,cal=False,fit_mesh=FIT,ref_mesh=REF):
    rng=np.random.default_rng(seed);ptrue=np.array([rng.uniform(.30,.40),rng.uniform(.60,.80),.15 if truth=='weak_rest' else 1.]);law='rest' if truth=='weak_rest' else truth
    js=profiles();keys=('train','val') if cal else ('train','val','test','extra');refs={};flux={};checks={};deltas={}
    for k in keys:
        v,c,p=simulate(js[k],'oracle',ptrue,law,ref_mesh,True);u,b,_=simulate(js[k],'oracle',ptrue,law,fit_mesh,True)
        refs[k]=v;flux[k]=p;checks[k]={'reference':c,'fit_truth':b};deltas[k]=float(np.max(abs(u-v))*1000)
    gate=all(healthy(c) for pair in checks.values() for c in pair.values()) and max(deltas.values())<=1
    row=dict(seed=seed,truth=truth,noise=noise,truth_params=ptrue.tolist(),truth_checks=checks,mesh_delta_mv=deltas,truth_gate_passed=gate,models={},validation_scores={})
    if not gate:return row
    y=refs['train']+rng.normal(0,noise/1000,refs['train'].shape);v=refs['val']+rng.normal(0,noise/1000,refs['val'].shape)
    for m in METHODS:
        f=fit(js['train'],y,m,'null',fit_mesh);p=f.x;pred,c,_=simulate(js['val'],m,p,'null',fit_mesh,True)
        score=float(np.mean(((pred-v)*1000/noise)**2));row['validation_scores'][m]=score
        model=dict(params=p.tolist(),success=bool(f.success),nfev=int(f.nfev),checks={'val':c})
        tr,tc,_=simulate(js['train'],m,p,'null',fit_mesh,True);model['checks']['train']=tc;model['train_rmse_mv']=rmse(tr,y)
        if not cal:
            grid=np.linspace(0,4,101);model['closure_rmse']=float(np.sqrt(np.mean((rates(m,p,'null',grid)[1]-ptrue[2]*missing(law,grid))**2)))
            for k in ('test','extra'):
                pred,c,q=simulate(js[k],m,p,'null',fit_mesh,True);model['checks'][k]=c;model[k+'_rmse_mv']=rmse(pred,refs[k])
                # Aggregate fine-cell reaction fluxes to matching coarse axial cells.
                n=fit_mesh[0];ratio=ref_mesh[0]//n
                assert ref_mesh[0]==ratio*n
                target=flux[k].reshape(len(js[k]),n,ratio,-1).sum(axis=2)
                model[k+'_reaction_density_rmse']=float(np.sqrt(np.mean((n*(q-target))**2)))
        model['physical_checks_passed']=all(healthy(c) for c in model['checks'].values());row['models'][m]=model
    row['fit_gate_passed']=all(x['success'] and x['physical_checks_passed'] for x in row['models'].values())
    row['raw'],row['gain']=select(row['validation_scores'],0.)
    return row

def run():
    numerical,_=verify();gate=all(x['passed'] for x in numerical);calibration=[];test=[];thresholds={};complete=gate
    if gate:
        for noise in NOISE:
            cal=[evaluate(s,'null',noise,True) for s in CAL_SEEDS];calibration.extend(cal)
            if not all(x['truth_gate_passed'] and x.get('fit_gate_passed',False) for x in cal):complete=False;break
            q=threshold([x['gain'] for x in cal]);thresholds[str(noise)]=q;print('threshold',noise,q,flush=True)
            for truth in TRUTHS:
                for seed in TEST_SEEDS:
                    row=evaluate(seed,truth,noise)
                    if row['truth_gate_passed'] and row.get('fit_gate_passed',False):row['gated']=select(row['validation_scores'],q)[0]
                    else:complete=False
                    test.append(row);print('test',noise,truth,seed,row.get('gated','failed'),flush=True)
    return dict(scope='synthetic reduced coupled x-r model; prospective null gate, no unique mechanism or experimental validation',environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),protocol=dict(fit_mesh=FIT,reference_mesh=REF,cal_seeds=CAL_SEEDS,test_seeds=TEST_SEEDS,truths=TRUTHS,noise=NOISE,methods=METHODS,alpha=ALPHA,base_ranges=[[.30,.40],[.60,.80]],weak_amplitude=.15),numerical_checks=numerical,numerical_gate_passed=gate,complete=complete,thresholds=thresholds,calibration=calibration,test=test)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();Path(a.out).write_text(json.dumps(run(),indent=2,allow_nan=False)+'\n')
