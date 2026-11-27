"""Corrected reduced x-r bridge with modal propagation."""
import argparse,json,platform
from pathlib import Path
import numpy as np
import scipy
from scipy.linalg import expm,eigh
from scipy.integrate import solve_ivp
from hybrid_p2d import DT,JS,BLOCKS,METHODS,profile,voltage,fit,rates,missing

def cell(j,n,m,reference=False):
    edges=np.linspace(0,1,m+1);w=np.diff(edges**3);rbar=.75*np.diff(edges**4)/w
    bs=np.array([[float(i>=k) for i in range(n)] for k in range(1,n)]);be=1-bs
    A=n*.35*np.eye(n)+.25/n*bs.T@bs+.7/n*be.T@be
    W=np.linalg.inv(A);one=np.ones(n);g=W@one/(one@W@one);P=W-np.outer(g,one@W);R=1/(one@W@one)
    L=np.zeros((m,m))
    for k in range(1,m):
        f=3*.06*(k/m)**2*m;L[k-1,k-1]-=f/w[k-1];L[k-1,k]+=f/w[k-1];L[k,k-1]+=f/w[k];L[k,k]-=f/w[k]
    s=np.zeros(m);e=(1-rbar[-1])/(rbar[-1]-rbar[-2]);s[-1]=1+e;s[-2]=-e
    b=np.zeros(m);b[-1]=n/w[-1]
    ev,Q=eigh(P);gg=Q.T@g
    M=L[None,:,:]-.8*ev[:,None,None]*np.outer(b,s)[None,:,:]
    h=gg[:,None]*b;aug=np.zeros((n,m+1,m+1));aug[:,:m,:m]=M;aug[:,:m,m]=h;E=expm(DT*aug)
    z=(Q.T@np.full((n,m),.5))[:,:,None]*np.ones((1,1,j.shape[1]));target=np.full(j.shape[1],.5)
    out=[];mass=charge=0.;lo=surflo=1.;hi=surfhi=0.
    for k,u in enumerate(j):
        J=JS*u;c=np.einsum('ab,bmc->amc',Q,z);surf=np.einsum('m,amc->ac',s,c);U=4.1-.8*surf;p=P@U+g[:,None]*J;V=g@U-R*J
        out.append(V-(.25+(.25+.7)/(2*n))*J)
        mass=max(mass,float(np.max(abs(np.einsum('m,amc->c',w,c)/n-target))));charge=max(charge,float(np.max(abs(p.sum(axis=0)-J))),float(np.max(abs(A@p+V[None,:]-U))))
        lo=min(lo,float(c.min()));hi=max(hi,float(c.max()));surflo=min(surflo,float(surf.min()));surfhi=max(surfhi,float(surf.max()))
        if k<len(j)-1:
            if reference:
                def rhs(t,y):
                    cc=y.reshape(n,m,-1);ss=np.einsum('m,amc->ac',s,cc);pp=P@(4.1-.8*ss)+g[:,None]*J
                    return (np.einsum('ij,ajc->aic',L,cc)+b[None,:,None]*pp[:,None,:]).ravel()
                sol=solve_ivp(rhs,(0,DT),c.ravel(),rtol=1e-10,atol=1e-12,method='DOP853');assert sol.success
                z=np.einsum('ab,bmc->amc',Q.T,sol.y[:,-1].reshape(n,m,-1))
            else:z=E[:,:m,:m]@z+E[:,:m,m,None]*J
            target+=DT*J
    return np.array(out),dict(mass=mass,charge=charge,min_c=lo,max_c=hi,min_surface=surflo,max_surface=surfhi)

MESHES=((8,12),(16,24),(32,48),(64,96),(128,192))
def run():
    js={k:profile(k) for k in BLOCKS};mesh={};bases={};rows=[]
    for k,j in js.items():
        v={};checks={}
        for n,m in MESHES:
            a,c=cell(j,n,m);v[n,m]=a;checks[str((n,m))]=c
            assert c['mass']<1e-9 and c['charge']<1e-9 and 0<c['min_c']<=c['max_c']<1 and 0<c['min_surface']<=c['max_surface']<1
        delta={str(a)+'->'+str(b):float(np.max(abs(v[a]-v[b]))*1000) for a,b in zip(MESHES,MESHES[1:])}
        a,_=cell(j,4,6);b,_=cell(j,4,6,True);ref=float(np.max(abs(a-b))*1000);assert ref<1e-5
        mesh[k]=dict(checks=checks,delta_mv=delta,time_reference_mv=ref);bases[k]=v
        print(k,delta,flush=True)
    gate=all(max(list(x['delta_mv'].values())[-2:])<=1 for x in mesh.values())
    if gate:
        for truth in ('null','rest','peak'):
            v={k:voltage(bases[k][128,192],j,'oracle',[.35,.7,1.],truth) for k,j in js.items()}
            for noise in (1.,5.):
                for seed in (11,23,37):
                    y=v['train']+np.random.default_rng(seed).normal(0,noise/1000,v['train'].shape)
                    for nm in ((8,12),(32,48),(128,192)):
                        for method in METHODS:
                            f=fit(bases['train'][nm],js['train'],y,method,truth);assert f.success
                            p=f.x;grid=np.linspace(0,4,101);d=rates(method,p,truth,grid)[1]
                            row=dict(truth=truth,noise=noise,seed=seed,mesh=list(nm),method=method,params=p.tolist(),success=bool(f.success),closure_rmse=float(np.sqrt(np.mean((d-missing(truth,grid))**2))))
                            for k,j in js.items():row[k+'_rmse_mv']=float(np.sqrt(np.mean(((voltage(bases[k][nm],j,method,p,truth)-(y if k=='train' else v[k]))*1000)**2)))
                            rows.append(row)
            print(truth,'fits done',flush=True)
    return dict(scope='synthetic reduced x-r bridge, terminal closure only; not full P2D',environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),mesh=mesh,mesh_gate_passed=gate,metrics=rows)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();Path(a.out).write_text(json.dumps(run(),indent=2,allow_nan=False)+'\n')
