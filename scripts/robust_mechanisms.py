"""Prospective mechanism competition under known IID/AR(1) measurement noise."""
import argparse,json,platform,math
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import least_squares
from robust_solver import simulate
from coupled_bridge import healthy,FIT,REF,rmse,rates,missing
from adaptive_coupled import profiles,threshold
METHODS=('calibrated','linear','rbf','diffusion','kinetic','series')
TRUTHS=('null','rest','peak','weak_rest','diffusion','kinetic','series')
RHOS=(0.,.8); SIGMA=5.; CAL=tuple(range(3000,3029)); NULL=tuple(range(4000,4024)); ALT=tuple(range(4100,4104))

def whiten(x,rho):
    z=x.copy();z[1:]=(x[1:]-rho*x[:-1])/np.sqrt(1-rho*rho);return z

def noise(rng,shape,rho):
    z=rng.normal(size=shape);e=z.copy()
    for k in range(1,len(e)):e[k]=rho*e[k-1]+np.sqrt(1-rho*rho)*z[k]
    return e*SIGMA/1000

def unpack(method,p):
    if method in ('linear','rbf'):return method,p,{}
    return 'calibrated',p[:2],({method:float(p[2])} if method!='calibrated' else {})

def predict(j,method,p,mesh,diagnostic=False):
    law,z,kw=unpack(method,p);return simulate(j,law,z,'null',mesh,diagnostic,**kw)

def truth_predict(j,truth,p,mesh):
    if truth in ('rest','peak','weak_rest'):
        return simulate(j,'oracle',p,'rest' if truth=='weak_rest' else truth,mesh,True)
    return predict(j,'calibrated' if truth=='null' else truth,p,mesh,True)

def fit_model(j,y,method,rho,mesh):
    if method in ('linear','rbf'):
        k=5 if method=='linear' else 4;lo=[.01,.05]+[0.]*k;hi=[1.5,3.]+[3.]*k;init=[.3,.7]+[.05]*k
    elif method=='calibrated':lo=[.01,.05];hi=[1.5,3.];init=[.3,.7]
    else:
        low,high,start={'diffusion':(.4,2.,1.),'kinetic':(.6,1.6,1.),'series':(0.,.5,.03)}[method]
        lo=[.01,.05,low];hi=[1.5,3.,high];init=[.3,.7,start]
    def residual(p):
        v,_,_=predict(j,method,p,mesh);r=whiten((v-y)*1000,rho).ravel()
        if method in ('linear','rbf'):r=np.r_[r,2*np.diff(rates(method,p,'null',np.linspace(0,3,31))[1],n=2)/.1**2]
        return r
    return least_squares(residual,init,bounds=(lo,hi),max_nfev=150,ftol=1e-7,xtol=1e-7,gtol=1e-7)

def decision(scores,q):
    best=min(METHODS[1:],key=scores.get);gain=scores['calibrated']-scores[best]
    return (best if gain>q else 'calibrated'),float(gain)

def evaluate(seed,truth,rho,cal=False,mesh=FIT,ref=REF):
    rng=np.random.default_rng(seed);a,b=rng.uniform(.30,.40),rng.uniform(.60,.80)
    extra={'null':1.,'rest':1.,'peak':1.,'weak_rest':.15,'diffusion':.65,'kinetic':1.25,'series':.12}[truth]
    p=np.array([a,b,extra]);js=profiles();keys=('train','val') if cal else ('train','val','test','extra')
    target={};flux={};deltas={};checks={}
    for k in keys:
        v,c,f=truth_predict(js[k],truth,p,ref);u,d,_=truth_predict(js[k],truth,p,mesh)
        target[k]=v;flux[k]=f;deltas[k]=float(np.max(abs(u-v))*1000);checks[k]={'reference':c,'fit_truth':d}
    gate=max(deltas.values())<=1 and all(healthy(c) for pair in checks.values() for c in pair.values())
    row=dict(seed=seed,truth=truth,rho=rho,truth_params=p.tolist(),mesh_delta_mv=deltas,truth_checks=checks,truth_gate_passed=gate,models={},validation_scores={})
    if not gate:return row
    y=target['train']+noise(rng,target['train'].shape,rho);v=target['val']+noise(rng,target['val'].shape,rho)
    for m in METHODS:
        f=fit_model(js['train'],y,m,rho,mesh);z=f.x;pred,c,_=predict(js['val'],m,z,mesh,True)
        row['validation_scores'][m]=float(np.mean(whiten((pred-v)*1000/SIGMA,rho)**2));model=dict(params=z.tolist(),success=bool(f.success),nfev=int(f.nfev),checks={'val':c})
        tr,tc,_=predict(js['train'],m,z,mesh,True);model['checks']['train']=tc;model['train_rmse_mv']=rmse(tr,y)
        if not cal:
            for k in ('test','extra'):
                pred,c,q=predict(js[k],m,z,mesh,True);model['checks'][k]=c;model[k+'_rmse_mv']=rmse(pred,target[k])
                n=mesh[0];ratio=ref[0]//n;assert ref[0]==ratio*n
                fref=flux[k].reshape(len(js[k]),n,ratio,-1).sum(axis=2);model[k+'_reaction_density_rmse']=float(np.sqrt(np.mean((n*(q-fref))**2)))
        model['physical_checks_passed']=all(healthy(c) for c in model['checks'].values());row['models'][m]=model
    row['fit_gate_passed']=all(m['success'] and m['physical_checks_passed'] for m in row['models'].values());row['raw'],row['gain']=decision(row['validation_scores'],0.)
    return row

def save(path,d):
    tmp=path.with_suffix('.part');tmp.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');tmp.replace(path)

def run(path):
    protocol=dict(rhos=RHOS,sigma_mv=SIGMA,cal_seeds=CAL,null_seeds=NULL,alternative_seeds=ALT,truths=TRUTHS,methods=METHODS,fit_mesh=FIT,reference_mesh=REF,alpha=.1,truth_extra={'rest':1.,'peak':1.,'weak_rest':.15,'diffusion':.65,'kinetic':1.25,'series':.12})
    d=dict(scope='synthetic reduced coupled model; known noise covariance and competing mechanisms; not real validation',environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),protocol=protocol,complete=False,thresholds={},calibration=[],test=[])
    # Atomic checkpoint after every case. No test-derived threshold changes.
    save(path,d)
    for rho in RHOS:
        cal=[]
        for s in CAL:
            row=evaluate(s,'null',rho,True);cal.append(row);d['calibration'].append(row);save(path,d);print('cal',rho,s,row.get('fit_gate_passed',False),flush=True)
        if not all(x['truth_gate_passed'] and x.get('fit_gate_passed',False) for x in cal):return d
        q=threshold([x['gain'] for x in cal]);d['thresholds'][str(rho)]=q;save(path,d)
        for t in TRUTHS:
            for s in NULL if t=='null' else ALT:
                row=evaluate(s,t,rho)
                if row['truth_gate_passed'] and row.get('fit_gate_passed',False):row['gated']=decision(row['validation_scores'],q)[0]
                d['test'].append(row);save(path,d);print('test',rho,t,s,row.get('gated','failed'),flush=True)
    d['complete']=all(x['truth_gate_passed'] and x.get('fit_gate_passed',False) for x in d['calibration']+d['test']);save(path,d);return d

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);run(Path(p.parse_args().out))
