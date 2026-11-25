"""Illustrative reduced x-r half-cell with terminal recovery closure."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares
DT=.25; JS=.025; RG=2.
BLOCKS={'train':[[.25,1.5,0,-3,.75,-1.5],[3,-.75,-1.5,0,.25,-3],[0,-.75,3,-.25,-1.5,.75],[1.5,-3,.25,-.75,0,3]],'test':[[.5,-2,0,1,-.5,2],[2,0,-1,.5,-2,1]],'extra':[[4,0,-2,-4,1,.5],[.5,-4,1,0,4,-2]]}
METHODS=('calibrated','linear','rbf','oracle')
def profile(k):
    j=np.repeat(np.array(BLOCKS[k],float).T,8,axis=0);return np.r_[j,j[-1:]]
def cell(j,n=4,m=6,reference=False):
    w=np.diff(np.linspace(0,1,m+1)**3);inv=np.tile(w/n,n)
    bs=np.array([[float(i>=k) for i in range(n)] for k in range(1,n)]);be=1-bs
    A=n*.35*np.eye(n)+.25/n*bs.T@bs+.7/n*be.T@be
    W=np.linalg.inv(A);one=np.ones(n);g=W@one/(one@W@one);P=W-np.outer(g,one@W);R=1/(one@W@one)
    L=np.zeros((m,m))
    for k in range(1,m):
        f=3*.06*(k/m)**2*m;L[k-1,k-1]-=f/w[k-1];L[k-1,k]+=f/w[k-1];L[k,k-1]+=f/w[k];L[k,k]-=f/w[k]
    S=np.eye(n*m)[m-1::m];B=S.T*n/w[-1];M=np.kron(np.eye(n),L)-.8*B@P@S;h=B@g
    aug=np.zeros((n*m+1,n*m+1));aug[:-1,:-1]=M;aug[:-1,-1]=h;E=expm(DT*aug)
    c=np.full((n*m,j.shape[1]),.5);out=[];mass=charge=0.;lo=1.;hi=0.;target=np.full(j.shape[1],.5)
    for k,u in enumerate(j):
        J=JS*u;U=4.1-.8*S@c;p=P@U+g[:,None]*J;V=g@U-R*J;out.append(V-.25*J)
        mass=max(mass,float(np.max(abs(inv@c-target))));charge=max(charge,float(np.max(abs(p.sum(axis=0)-J))),float(np.max(abs(A@p+V[None,:]-U))));lo=min(lo,float(c.min()));hi=max(hi,float(c.max()))
        if k<len(j)-1:
            if reference:
                sol=solve_ivp(lambda t,y:(M@y.reshape(c.shape)+h[:,None]*J).ravel(),(0,DT),c.ravel(),rtol=1e-11,atol=1e-13);assert sol.success;c=sol.y[:,-1].reshape(c.shape)
            else:c=E[:-1,:-1]@c+E[:-1,-1,None]*J
            target+=DT*J
    return np.array(out),dict(mass=mass,charge=charge,min_c=lo,max_c=hi)
def missing(t,u):
    if t=='null':return np.zeros_like(u)
    if t=='rest':return .4/(1+(u/.8)**2)
    if t=='peak':return .04+.4*np.exp(-(u-1.2)**2/.65)
    raise ValueError(t)
def rates(m,p,t,u):
    a=p[0]*u*u/(1+p[1]*u*u)
    if m=='calibrated':d=np.zeros_like(u)
    elif m=='linear':d=np.interp(u,[0,.25,.75,1.5,3],p[2:])
    elif m=='rbf':d=np.exp(-((u[...,None]-np.array([0,.8,1.6,3]))/.8)**2)@p[2:]
    elif m=='oracle':d=p[2]*missing(t,u)
    else:raise ValueError(m)
    return a,d
def closure(j,m,p,t):
    a,d=rates(m,p,t,abs(j));x=np.zeros(j.shape[1]);out=[x.copy()]
    for k in range(len(j)-1):
        z=a[k]+d[k];x=x*np.exp(-z*DT)+np.divide(a[k]*(-np.expm1(-z*DT)),z,out=np.zeros_like(z),where=z>0);out.append(x.copy())
    return np.array(out)
def voltage(base,j,m,p,t):return base-RG*JS*j*closure(j,m,p,t)
def fit(base,j,y,m,t):
    count={'calibrated':0,'linear':5,'rbf':4,'oracle':1}[m];p=np.r_[.3,.7,np.full(count,.05 if m!='oracle' else .8)]
    def res(z):
        r=((voltage(base,j,m,z,t)-y)*1000).ravel()
        if m in ('linear','rbf'):r=np.r_[r,2*np.diff(rates(m,z,t,np.linspace(0,3,31))[1],n=2)/.1**2]
        return r
    return least_squares(res,p,bounds=(np.r_[.01,.05,np.zeros(count)],np.r_[1.5,3.,np.full(count,3.)]),max_nfev=250,ftol=1e-8,xtol=1e-8,gtol=1e-8)
def run():
    js={k:profile(k) for k in BLOCKS};base={};checks={}
    for k,j in js.items():
        base[k],a=cell(j);ref,_=cell(j,reference=True);fine,_=cell(j,8,12);a.update(time_reference_mv=float(np.max(abs(base[k]-ref))*1000),mesh_delta_mv=float(np.max(abs(base[k]-fine))*1000));checks[k]=a
        assert a['mass']<1e-10 and a['charge']<1e-10 and 0<a['min_c']<=a['max_c']<1
    rows=[]
    for t in ('null','rest','peak'):
        v={k:voltage(base[k],j,'oracle',[.35,.7,1.],t) for k,j in js.items()}
        for noise in (1.,5.):
            for seed in (11,23,37):
                y=v['train']+np.random.default_rng(seed).normal(0,noise/1000,v['train'].shape)
                for m in METHODS:
                    f=fit(base['train'],js['train'],y,m,t);p=f.x;grid=np.linspace(0,4,101);d=rates(m,p,t,grid)[1];pred={k:voltage(base[k],j,m,p,t) for k,j in js.items()};xs={k:closure(j,m,p,t) for k,j in js.items()}
                    row=dict(truth=t,noise=noise,seed=seed,method=m,success=bool(f.success),params=p.tolist(),closure_rmse=float(np.sqrt(np.mean((d-missing(t,grid))**2))),min_x=float(min(x.min() for x in xs.values())),max_x=float(max(x.max() for x in xs.values())))
                    row.update({k+'_rmse_mv':float(np.sqrt(np.mean(((pred[k]-(y if k=='train' else v[k]))*1000)**2))) for k in js});rows.append(row)
    return dict(scope='synthetic reduced x-r FV half-cell, terminal closure, not full P2D validation',checks=checks,metrics=rows)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();Path(a.out).write_text(json.dumps(run(),indent=2,allow_nan=False)+'\n')
