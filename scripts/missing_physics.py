"""Synthetic missing interface recovery mechanism, not experimental validation."""
import argparse,json,platform
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import least_squares
from scipy.integrate import solve_ivp
from dynamic_benchmark import profiles,observe,rmse
TRUTHS=('null','rest','peak'); METHODS=('nominal','calibrated','constant','linear','hybrid_rbf','oracle')
SEEDS=(11,23,37); NOISE=(1.,5.); LAMS=(0.,10.,50.)
NODES=np.array([0.,.25,.75,1.5,3.]); CENTERS=np.array([0.,.75,1.5,3.]); GRID=np.linspace(0,3,31)
def make_profiles(blocks):
    j=np.repeat(np.array(blocks,float).T,6,axis=0);return np.r_[j,j[-1:]]
def design():
    return dict(train=np.c_[profiles('train'),profiles('history')],val=make_profiles([[1.2,0,.4,2.4,0,.9],[2.4,.9,0,-1.2,.4,0]]),interp=profiles('interp'),extra=profiles('extra'),recovery=make_profiles([[2,0,0,.5,0,1],[1,0,0,.5,0,1]]))
def missing(name,j):
    j=np.asarray(j)
    if name=='null':return np.zeros_like(j)
    if name=='rest':return .10/(1+(j/.8)**2)
    if name=='peak':return .012+.09*np.exp(-(j-1.2)**2/.65)
    raise ValueError(name)
def rates(method,p,truth,j):
    j=np.asarray(j);a,b,c=p[:3];growth=a*j*j/(1+b*j*j)
    if method in ('nominal','calibrated'):d=np.zeros_like(j)
    elif method=='constant':d=np.full_like(j,p[3])
    elif method=='linear':d=np.interp(j,NODES,p[3:])
    elif method=='hybrid_rbf':d=np.exp(-((j[...,None]-CENTERS)/.8)**2)@p[3:]
    else:d=p[3]*missing(truth,j)
    return growth,c,d
def simulate(j,method,p,truth,reference=False,steps=2):
    a,c,d=rates(method,p,truth,abs(j[:-1]));x=np.zeros(j.shape[1]);out=[x.copy()];dt=1/steps
    for ak,dk in zip(a,d):
        def f(v):return ak*(1-v)-c*v**3-dk*v
        if reference:
            s=solve_ivp(lambda t,v:f(v),(0,1),x,rtol=1e-11,atol=1e-13)
            if not s.success:raise RuntimeError(s.message)
            x=s.y[:,-1]
        else:
            for _ in range(steps):
                k1=f(x);k2=f(x+dt*k1/2);k3=f(x+dt*k2/2);k4=f(x+dt*k3);x=x+dt*(k1+2*k2+2*k3+k4)/6
        out.append(x.copy())
    return np.array(out)
def fit(method,truth,j,y,lam=0.):
    n={'calibrated':0,'constant':1,'linear':5,'hybrid_rbf':4,'oracle':1}[method]
    init=np.r_[.1,.7,.06,np.full(n,1. if method=='oracle' else .015)]
    lo=np.r_[.005,.03,0.,np.zeros(n)];hi=np.r_[.4,4.,.4,np.full(n,3. if method=='oracle' else .25)]
    def fun(p):
        e=(observe(j,simulate(j,method,p,truth))-y).ravel()
        if lam:
            d=rates(method,p,truth,GRID)[2];e=np.r_[e,lam*np.diff(d,n=2)/.1**2]
        return e
    f=least_squares(fun,init,bounds=(lo,hi),max_nfev=120,ftol=1e-8,xtol=1e-8,gtol=1e-8)
    return f.x,bool(f.success),int(f.nfev)
def run():
    js=design();rows=[];checks=[];candidates=[]
    for truth in TRUTHS:
        ptrue=[.1,.7,.06,1.];xs={k:simulate(j,'oracle',ptrue,truth,True) for k,j in js.items()};vs={k:observe(js[k],x) for k,x in xs.items()}
        err=max(rmse(simulate(j,'oracle',ptrue,truth),xs[k]) for k,j in js.items());assert err<1e-6;checks.append(dict(truth=truth,state_rmse=err))
        for noise in NOISE:
            for seed in SEEDS:
                rng=np.random.default_rng(seed);y=vs['train']+rng.normal(0,noise,vs['train'].shape);v=vs['val']+rng.normal(0,noise,vs['val'].shape)
                for method in METHODS:
                    opts=[]
                    for lam in (LAMS if method in ('linear','hybrid_rbf') else (0.,)):
                        if method=='nominal':p,ok,n=[.1,.7,.06],True,0
                        else:p,ok,n=fit(method,truth,js['train'],y,lam)
                        score=rmse(observe(js['val'],simulate(js['val'],method,p,truth)),v)
                        candidates.append(dict(truth=truth,noise=noise,seed=seed,method=method,lam=lam,success=ok,nfev=n,val_rmse_mv=score))
                        if ok:opts.append((score,lam,p))
                    if not opts:raise RuntimeError(f'no converged candidate: {truth} {noise} {seed} {method}')
                    score,lam,p=min(opts,key=lambda o:o[0]);xp={k:simulate(j,method,p,truth) for k,j in js.items()};vp={k:observe(js[k],x) for k,x in xp.items()};grid=np.linspace(0,4,101);d=rates(method,p,truth,grid)[2]
                    row=dict(truth=truth,noise=noise,seed=seed,method=method,lam=lam,params=list(p),val_rmse_mv=score,train_rmse_mv=rmse(vp['train'],y),interp_rmse_mv=rmse(vp['interp'],vs['interp']),extra_rmse_mv=rmse(vp['extra'],vs['extra']),recovery_rmse_mv=rmse(vp['recovery'],vs['recovery']),closure_rmse=rmse(d,missing(truth,grid)),rest_closure=float(d[0]),latent_rmse=rmse(xp['recovery'],xs['recovery']),min_state=float(min(x.min() for x in xp.values())),max_state=float(max(x.max() for x in xp.values())))
                    assert all(np.isfinite(z) for z in row.values() if isinstance(z,float)) and 0<=row['min_state']<=row['max_state']<=1
                    rows.append(row)
                print(truth,noise,seed,flush=True)
    return dict(scope='synthetic missing state-dependent recovery term, known observation map and closure placement; not experimental validation',environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),protocol=dict(truths=TRUTHS,methods=METHODS,seeds=SEEDS,noise=NOISE,lambdas=LAMS,profiles={k:j.tolist() for k,j in js.items()}),checks=checks,candidates=candidates,metrics=rows)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();Path(a.out).write_text(json.dumps(run(),indent=2,allow_nan=False)+'\n')
