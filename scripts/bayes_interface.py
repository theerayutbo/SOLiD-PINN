"""Bayesian calibration of the v0.8.3 analytic synthetic model (not Bayesian PINN)."""
import argparse, json, platform
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import least_squares
from scipy.special import logsumexp
P=np.array([25.,12.,15.,.8]); LO=np.array([1.,1.,2.,.1]); HI=np.array([60.,60.,80.,5.]); K=4*8.314*298.15/96485*1000

def voltage(t,j,p):
    return 2*j*(p[...,1,None]+(p[...,0,None]-p[...,1,None])*np.exp(-t/p[...,2,None]))+K*np.arcsinh(j/(2*p[...,3,None]))

def design(name):
    if name=='matched':
        t=np.repeat(np.arange(30.),2); j=(np.tile([.25,.5,1.,2.,4.],6)[:,None]*[-1.,1.]).ravel()
    elif name in ('single','multi'):
        a=np.array([1.] if name=='single' else [.25,.5,1.,2.,4.]);t,j=np.meshgrid(np.arange(30.),np.r_[-a,a],indexing='ij');t=t.ravel();j=j.ravel()
    else: raise ValueError('unknown design')
    return t,j

def weights(x):
    dx=np.diff(x);return np.r_[dx[0]/2,(dx[:-1]+dx[1:])/2,dx[-1]/2]

def axis(lo,hi,center,sd,n,log=False):
    base=np.geomspace(lo,hi,n) if log else np.linspace(lo,hi,n)
    if np.isfinite(sd) and sd>0:
        local=np.linspace(max(lo,center-10*sd),min(hi,center+10*sd),n)
        base=np.unique(np.r_[base,local,center])
    return base

def posterior(t,j,y,sigma,prior='uniform',n=151,draws=16000,seed=123):
    if sigma<=0 or prior not in ('uniform','log_j0'):raise ValueError('invalid noise/prior')
    fits=[least_squares(lambda p:(voltage(t,j,p)-y)/sigma,x,bounds=(LO,HI),x_scale='jac') for x in ([20,10,10,.5],[35,20,30,2],[10,5,5,.3])]
    f=min((f for f in fits if f.success),key=lambda q:q.cost)
    cov=np.linalg.pinv(f.jac.T@f.jac,rcond=1e-10);sd=np.sqrt(np.maximum(0,np.diag(cov)))
    single=np.ptp(abs(j))<1e-12
    tau=axis(LO[2],HI[2],f.x[2],sd[2],n)
    j0=axis(LO[3],HI[3],f.x[3],np.inf if single else sd[3],n,log=True)
    x=np.exp(-t[None,:]/tau[:,None]); X=np.stack([2*j*x,2*j*(1-x)],axis=-1)
    gram=np.einsum('tni,tnj->tij',X,X); inv=np.linalg.inv(gram)
    Y=y[None,:]-K*np.arcsinh(j[None,:]/(2*j0[:,None]))
    xy=np.einsum('tni,kn->tki',X,Y,optimize=True);mu=np.einsum('tij,tkj->tki',inv,xy)
    sse=np.maximum(0,np.sum(Y*Y,axis=1)[None,:]-np.sum(mu*xy,axis=-1))
    lp=-sse/(2*sigma**2)-.5*np.linalg.slogdet(gram)[1][:,None]+np.log(weights(tau))[:,None]+np.log(weights(j0))[None,:]
    if prior=='log_j0':lp-=np.log(j0)[None,:]
    prob=np.exp(lp-logsumexp(lp)); rng=np.random.default_rng(seed);chol=np.linalg.cholesky(inv)*sigma
    chunks=[];accepted=attempted=0
    for _ in range(50):
        ids=rng.choice(prob.size,size=draws,p=prob.ravel());a,b=np.unravel_index(ids,prob.shape)
        rr=mu[a,b]+np.einsum('nij,nj->ni',chol[a],rng.normal(size=(draws,2)))
        ok=np.all((rr>=LO[:2])&(rr<=HI[:2]),axis=1);attempted+=draws;accepted+=ok.sum();chunks.append(np.column_stack((rr[ok],tau[a[ok]],j0[b[ok]])))
        if accepted>=draws:break
    if accepted<draws:raise RuntimeError('insufficient bounded posterior draws')
    p=np.concatenate(chunks)[:draws]
    q=np.quantile(p,[.025,.5,.975],axis=0)
    return p,dict(quantiles=q.tolist(),acceptance=float(accepted/attempted),grid=[len(tau),len(j0)],ls=f.x.tolist())

def summarize(p,meta):
    t=np.array([40.,40.]);j=np.array([1.,3.]);z=voltage(t,j,p);q=np.quantile(z,[.025,.5,.975],axis=0);truth=voltage(t,j,P)
    meta.update(pred_quantiles=q.tolist(),pred_truth=truth.tolist(),covered=((np.array(meta['quantiles'])[0]<=P)&(P<=np.array(meta['quantiles'])[2])).tolist(),pred_covered=((q[0]<=truth)&(truth<=q[2])).tolist())
    return meta

def run(n=151,draws=16000,repeats=30):
    rows=[]; checks=[]; coverage=[]
    for name in ('single','matched','multi'):
        t,j=design(name)
        for sigma in (1.,5.):
            y=voltage(t,j,P)+np.random.default_rng(11).normal(0,sigma,len(t))
            for prior in ('uniform','log_j0'):
                p,m=posterior(t,j,y,sigma,prior,n,draws,123)
                rows.append(dict(design=name,noise=sigma,prior=prior,**summarize(p,m)))
                if prior=='uniform':
                    p2,m2=posterior(t,j,y,sigma,prior,n*2-1,draws*2,456)
                    checks.append(dict(design=name,noise=sigma,coarse=m['quantiles'],fine=m2['quantiles'],delta_over_width=(np.abs(np.array(m['quantiles'])-np.array(m2['quantiles']))/np.maximum(1e-12,np.ptp(np.array(m2['quantiles'])[[0,2]],axis=0))).tolist()))
        for seed in range(100,100+repeats):
            sigma=5.;y=voltage(t,j,P)+np.random.default_rng(seed).normal(0,sigma,len(t));p,m=posterior(t,j,y,sigma,'uniform',n,draws,seed+10000);coverage.append(dict(design=name,seed=seed,**summarize(p,m)))
        print(name,'done',flush=True)
    return dict(truth=P.tolist(),model='analytic v0.8.3 symmetric-cell ODE',n=n,draws=draws,repeats=repeats,coverage_noise_mv=5,representative_seed=11,parameters=['R0','Rinf','tau','j0'],environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),representative=rows,grid_checks=checks,coverage=coverage)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--n',type=int,default=151);p.add_argument('--draws',type=int,default=16000);p.add_argument('--repeats',type=int,default=30);a=p.parse_args();Path(a.out).write_text(json.dumps(run(a.n,a.draws,a.repeats),indent=2)+'\n')
