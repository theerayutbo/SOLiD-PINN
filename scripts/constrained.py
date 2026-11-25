"""Validation-selected neural rate learning from synthetic dynamic current."""
import argparse,json,platform,time
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import least_squares
from scipy.interpolate import PchipInterpolator
from dynamic_benchmark import profiles, reference, integrate, observe, true_rate, rmse, LEVELS
TRUTHS=('rational','exponential','peak')
NOISE=(1.,5.); NOISE_SEEDS=(11,23,37); INIT_SEEDS=(101,202)
LAM=(0.,2.,20.); GRID=np.linspace(0,3,31)
METHODS=('pchip','free','smooth','monotone')
VAL_BLOCKS=[[.4,1.2,0,-2.4,.9,1.8],[-2.4,0,.4,-1.2,1.8,.9]]

def validation():
    j=np.repeat(np.array(VAL_BLOCKS,float).T,6,axis=0);return np.r_[j,j[-1:]]

def law(name,j):
    if name=='peak':
        z=np.asarray(j)**2
        return .16*z*np.exp(-z/3.0)+.035*z/(1+z)
    return true_rate(name,j)

def rate_fn(method,p):
    if method=='pchip':
        f=PchipInterpolator(LEVELS,np.r_[0,p]);return lambda j:f(np.clip(j,0,3))
    def neural(j):
        z=np.asarray(j)**2/(1+np.asarray(j)**2)
        if method=='monotone':
            w=np.logaddexp(0,p[:3]);v=np.logaddexp(0,p[6:9]);h=np.tanh(z[:,None]*w+p[3:6]);return z*np.logaddexp(0,h@v+p[9])
        h=np.tanh(z[:,None]*p[:3]+p[3:6]);return z*np.logaddexp(0,h@p[6:9]+p[9])
    return neural

def nodal_fit(j,y):
    def residual(p):return (observe(j,integrate(j,rate_fn('pchip',p)))-y).ravel()
    f=least_squares(residual,[.006,.04,.09,.12],bounds=(np.zeros(4),np.full(4,.35)),max_nfev=120,ftol=1e-9,xtol=1e-9,gtol=1e-9)
    if not f.success:raise RuntimeError(f.message)
    return f

def fit(method,nodal,seed,lam):
    # Gauss-Newton local approximation to voltage objective: residual offset retained.
    r=np.random.default_rng(seed);init=np.r_[r.normal(0,1,6),r.normal(0,.2,3),-2. if method!='monotone' else -3.]
    def residual(p):
        rate=rate_fn(method,p);e=nodal.fun+nodal.jac@(rate(LEVELS[1:])-nodal.x)
        e=np.r_[e,.15*(p-init)]
        if lam:e=np.r_[e,lam*np.diff(rate(GRID),n=2)/(.1**2)]
        return e
    f=least_squares(residual,init,bounds=(-8.,8.),max_nfev=250,ftol=1e-7,xtol=1e-7,gtol=1e-7)
    if not np.isfinite(f.cost):raise RuntimeError('nonfinite fit')
    return f

def run():
    js={k:profiles(k) for k in ('train','interp','extra','history')};js['val']=validation();rows=[];candidates=[];checks=[]
    for truth in TRUTHS:
        r=lambda j:law(truth,j);xs={k:reference(j,r) for k,j in js.items()};vs={k:observe(j,xs[k]) for k,j in js.items()}
        err=max(rmse(integrate(j,r),xs[k]) for k,j in js.items());assert err<1e-6;checks.append(dict(truth=truth,rk4_error=err))
        for noise in NOISE:
            for ns in NOISE_SEEDS:
                rng=np.random.default_rng(ns);y=vs['train']+rng.normal(0,noise,vs['train'].shape);val=vs['val']+rng.normal(0,noise,vs['val'].shape)
                nodal=nodal_fit(js['train'],y)
                for method in METHODS:
                    seeds=(None,) if method=='pchip' else INIT_SEEDS;lamlist=LAM if method in ('smooth','monotone') else (0.,)
                    for seed in seeds:
                        start=time.monotonic();opts=[]
                        for lam in lamlist:
                            f=nodal if method=='pchip' else fit(method,nodal,seed,lam);rate=rate_fn(method,f.x);score=rmse(observe(js['val'],integrate(js['val'],rate)),val)
                            candidates.append(dict(truth=truth,noise_mv=noise,noise_seed=ns,init_seed=seed,method=method,lam=lam,val_rmse_mv=score,success=bool(f.success),nfev=int(f.nfev)))
                            if f.success:opts.append((score,lam,f))
                        if not opts:raise RuntimeError('no converged candidate')
                        score,lam,f=min(opts,key=lambda z:z[0]);rate=rate_fn(method,f.x)
                        xp={k:integrate(j,rate) for k,j in js.items()};vp={k:observe(j,xp[k]) for k,j in js.items()};grid=np.linspace(0,4,101);pred=rate(grid)
                        rows.append(dict(truth=truth,noise_mv=noise,noise_seed=ns,init_seed=seed,method=method,selected_lambda=lam,success=bool(f.success),validation_rmse_mv=score,train_rmse_mv=rmse(vp['train'],y),interp_rmse_mv=rmse(vp['interp'],vs['interp']),extra_rmse_mv=rmse(vp['extra'],vs['extra']),history_rmse_mv=rmse(vp['history'],vs['history']),latent_rmse=rmse(xp['interp'],xs['interp']),rate_rmse=rmse(pred,r(grid)),min_rate=float(pred.min()),min_rate_increment=float(np.diff(pred).min()),min_state=float(min(x.min() for x in xp.values())),max_state=float(max(x.max() for x in xp.values())),params=f.x.tolist(),seconds=time.monotonic()-start))
                print(truth,noise,ns,'done',flush=True)
    return dict(scope='synthetic known observation map and dynamics; local Gauss-Newton nodal rate surrogate, no experimental validation',environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),protocol=dict(truths=TRUTHS,noise=NOISE,noise_seeds=NOISE_SEEDS,init_seeds=INIT_SEEDS,lambdas=LAM,val_blocks=VAL_BLOCKS,methods=METHODS),checks=checks,metrics=rows,candidates=candidates)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();Path(a.out).write_text(json.dumps(run(),indent=2,allow_nan=False)+'\n')
