"""Synthetic piecewise-current benchmark; voltage-only fit, known observation map."""
import argparse,json,platform,time
from pathlib import Path
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.interpolate import PchipInterpolator
from scipy.optimize import least_squares
from scipy.special import expit
K=4*8.314*298.15/96485*1000; C=.06; GAIN=18.; J0=.8
LEVELS=np.array([0.,.25,.75,1.5,3.]); T=np.arange(37.)
# 6-hour blocks, including rests and reversals; four train, two per test group.
BLOCKS={
 'train':[[.25,1.5,0,3,-.75,1.5],[3,.75,-1.5,0,.25,-3],[0,-.75,3,.25,-1.5,.75],[1.5,-3,.25,-.75,0,3]],
 'interp':[[.5,-2,0,1,-.5,2],[2,0,-1,.5,-2,1]],
 'extra':[[4,0,-2,4,-1,.5],[.5,-4,1,0,4,-2]],
 'history':[[3,0,0,.75,.75,.75],[.25,0,0,.75,.75,.75]],
}
METHODS=('stateless','misspecified','pchip','oracle','neural_ode')
TRUTHS=('rational','exponential')
NOISE=(1.,5.); SEEDS=(11,23,37)

def profiles(name):
    j=np.repeat(np.array(BLOCKS[name],float).T,6,axis=0)
    return np.concatenate([j,j[-1:]],axis=0)

def true_rate(name,j):
    z=np.asarray(j)**2
    if name=='rational':return .1*z/(1+.7*z)
    if name=='exponential':return .12*(-np.expm1(-z/.9))
    raise ValueError(name)

def observe(j,x):
    return 2*j*(12+13*np.exp(-T[:len(j),None]/15)+GAIN*x)+K*np.arcsinh(j/(2*J0))

def reference(j,rate):
    x=np.zeros(j.shape[1]);out=[x.copy()]
    for u in j[:-1]:
        a=rate(abs(u)); sol=solve_ivp(lambda t,x:a*(1-x)-C*x**3,(0,1),x,rtol=1e-11,atol=1e-13)
        if not sol.success:raise RuntimeError(sol.message)
        x=sol.y[:,-1];out.append(x.copy())
    return np.array(out)

def integrate(j,rate,steps=2,static=False):
    u,ids=np.unique(abs(j),return_inverse=True);a=rate(u)[ids.reshape(j.shape)]
    # Static baseline assumes every observation belongs to a constant-current trajectory from time zero.
    if static:
        x=np.zeros(len(u));out=[x[ids.reshape(j.shape)[0]]]; ar=rate(u)
    else:x=np.zeros(j.shape[1]);out=[x.copy()]
    dt=1/steps
    for k in range(len(j)-1):
        ak=ar if static else a[k]
        def f(v):return ak*(1-v)-C*v**3
        for _ in range(steps):
            k1=f(x);k2=f(x+dt*k1/2);k3=f(x+dt*k2/2);k4=f(x+dt*k3);x=x+dt*(k1+2*k2+2*k3+k4)/6
        out.append(x[ids.reshape(j.shape)[k+1]] if static else x.copy())
    return np.array(out)

def rate_fn(method,p,truth):
    if method=='misspecified':return lambda j:p[0]*np.asarray(j)**2
    if method=='oracle':
        if truth=='rational':return lambda j:p[0]*j*j/(1+p[1]*j*j)
        return lambda j:p[0]*(-np.expm1(-j*j/p[1]))
    if method in ('pchip','stateless'):
        f=PchipInterpolator(LEVELS,np.r_[0,p]);return lambda j:f(np.clip(j,0,3))
    # Train all 10 parameters of a three-unit tanh MLP. Bounded input gives a saturation inductive bias.
    def neural(j):
        z=j*j/(1+j*j);h=np.tanh(z[:,None]*p[:3]+p[3:6]);return z*np.logaddexp(0,h@p[6:9]+p[9])
    return neural

def fit(method,truth,j,y,seed):
    if method=='misspecified':init=[.015];lo=[1e-6];hi=[.1]
    elif method=='oracle':init=[.08,.8];lo=[.001,.05];hi=[.4,5.]
    elif method in ('pchip','stateless'):init=[.006,.04,.09,.12];lo=[0.]*4;hi=[.35]*4
    else:
        rng=np.random.default_rng(seed);init=np.r_[rng.normal(0,1,6),rng.normal(0,.2,3),-2.];lo=[-8.]*10;hi=[8.]*10
    init=np.array(init)
    def residual(p):
        v=observe(j,integrate(j,rate_fn(method,p,truth),static=method=='stateless'))
        r=(v-y).ravel()
        if method=='neural_ode':r=np.r_[r,.15*(p-init)] # fixed predeclared regularization, in mV residual units
        return r
    f=least_squares(residual,init,bounds=(lo,hi),max_nfev=160,ftol=1e-7,xtol=1e-7,gtol=1e-7)
    if not np.isfinite(f.cost):raise RuntimeError('nonfinite fit')
    return rate_fn(method,f.x,truth),f

def rmse(x,y):return float(np.sqrt(np.mean((x-y)**2)))

def run():
    js={name:profiles(name) for name in BLOCKS};rows=[];checks=[]
    for truth in TRUTHS:
        rr=lambda j:true_rate(truth,j); xs={k:reference(j,rr) for k,j in js.items()};vs={k:observe(j,xs[k]) for k,j in js.items()}
        err=max(rmse(integrate(j,rr),xs[k]) for k,j in js.items());checks.append(dict(truth=truth,rk4_state_rmse=err));assert err<1e-6
        # At 24 h both history profiles have identical current but different earlier current.
        for noise in NOISE:
            for seed in SEEDS:
                y=vs['train']+np.random.default_rng(seed).normal(0,noise,vs['train'].shape)
                for method in METHODS:
                    start=time.monotonic();rate,f=fit(method,truth,js['train'],y,seed)
                    xp={k:integrate(j,rate,static=method=='stateless') for k,j in js.items()};vp={k:observe(j,xp[k]) for k,j in js.items()}
                    hist=vp['history'][24,0]-vp['history'][24,1];actual=vs['history'][24,0]-vs['history'][24,1]
                    row=dict(truth=truth,noise_mv=noise,seed=seed,method=method,success=bool(f.success),nfev=int(f.nfev),train_rmse_mv=rmse(vp['train'],y),interp_rmse_mv=rmse(vp['interp'],vs['interp']),extra_rmse_mv=rmse(vp['extra'],vs['extra']),history_rmse_mv=rmse(vp['history'],vs['history']),history_delta_mv=float(hist),history_truth_mv=float(actual),rest_state_rmse=rmse(xp['interp'][js['interp']==0],xs['interp'][js['interp']==0]),latent_rmse=rmse(xp['interp'],xs['interp']),rate_rmse=rmse(rate(np.array([.5,1.,2.,4.])),rr(np.array([.5,1.,2.,4.]))),min_state=float(min(x.min() for x in xp.values())),max_state=float(max(x.max() for x in xp.values())),params=f.x.tolist(),seconds=time.monotonic()-start)
                    if not all(np.isfinite(v) for v in row.values() if isinstance(v,float)):raise RuntimeError('nonfinite result')
                    rows.append(row)
                print(truth,noise,seed,'done',flush=True)
    return dict(scope='synthetic dynamic current, known observation map; not experimental validation',environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),protocol=dict(blocks=BLOCKS,block_hours=6,measurement_hours=T.tolist(),noise_mv=NOISE,seeds=SEEDS,truths=TRUTHS,methods=METHODS,train_points=int(js['train'].size),known_C=C,known_gain=GAIN,known_j0=J0),checks=checks,metrics=rows)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();Path(a.out).write_text(json.dumps(run(),indent=2,allow_nan=False)+'\n')
