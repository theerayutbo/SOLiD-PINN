"""Synthetic single-ion x-r FVM with independent active inventory and BV kinetics."""
from dataclasses import dataclass, asdict
import json
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import root

@dataclass(frozen=True)
class Params:
    L:float=60e-6; S:float=150e-6; R:float=6e-6; A:float=1e-4
    eps:float=.35; ionic:float=.40; electronic:float=.20; void:float=.05
    rho:float=4800.; cmax:float=45000.; D:float=5e-15
    ksep:float=.08; kcat:float=.004; scat:float=.08; j0:float=.5; jli:float=10.
    T:float=298.15; F:float=96485.33212; gas:float=8.314462618
    qnom:float=150.; low:float=2.8; high:float=4.15
    @property
    def mass_g(self):return 1000*self.rho*self.eps*self.L*self.A
    @property
    def inventory(self):return self.F*self.cmax/(3600*self.rho)
    def current_density(self,rate):return self.qnom*self.mass_g/1000/self.A/rate
    def validate(self):
        if abs(self.eps+self.ionic+self.electronic+self.void-1)>1e-12 or self.void<0:raise ValueError('phase fractions')
        if min(self.eps,self.ionic,self.electronic,self.D,self.ksep,self.kcat,self.scat,self.j0,self.jli,self.rho,self.cmax,self.L,self.R,self.S,self.A,self.T)<=0:raise ValueError('positive parameters required')

class Solver:
    def __init__(self,p=Params(),nx=4,nr=12):
        p.validate();self.p=p;self.n=nx;self.m=nr;self.dx=p.L/nx;self.a=3*p.eps/p.R
        self.beta=p.F/(2*p.gas*p.T);r=np.linspace(0,p.R,nr+1);w=np.diff(r**3)/3;self.w=w/w.sum();L=np.zeros((nr,nr))
        for k in range(1,nr):
            g=p.D*r[k]**2/(r[k+1]-r[k]);L[k-1,k-1]-=g/w[k-1];L[k-1,k]+=g/w[k-1];L[k,k-1]+=g/w[k];L[k,k]-=g/w[k]
        self.L=L;self.b=np.zeros(nr);self.b[-1]=r[-1]**2/w[-1]/(self.a*self.dx*p.F*p.cmax)
        rc=.75*np.diff(r**4)/np.diff(r**3);self.e=(p.R-rc[-1])/(rc[-1]-rc[-2]);one=np.ones((nx,nx));bs=np.array([[float(i<k) for i in range(nx)] for k in range(1,nx)]);be=1-bs
        self.K=self.dx*((be.T@be+.5*one)/p.kcat+(bs.T@bs+.5*one)/p.scat)
    def fields(self,c,J):
        p=self.p;surf=c[:,-1]+self.e*(c[:,-1]-c[:,-2]);u=4.4-1.9*surf;scale=2*p.j0*self.a*self.dx
        ext=J*p.S/p.ksep+np.arcsinh(J/(2*p.jli))/self.beta
        def res(z):
            q=z[:-1];return np.r_[self.K@q+np.arcsinh(q/scale)/self.beta+z[-1]-u,q.sum()-J]
        def jac(z):return np.block([[self.K+np.diag(1/(self.beta*np.sqrt(scale**2+z[:-1]**2))),np.ones((self.n,1))],[np.ones((1,self.n)),np.zeros((1,1))]])
        z=root(res,np.r_[np.full(self.n,J/self.n),u.mean()],jac=jac,tol=1e-10).x
        err=float(np.max(abs(res(z))))
        if err>1e-8 or not np.isfinite(err):raise RuntimeError('reaction solve failed')
        return z[-1]-ext,z[:-1],surf,err
    def stage(self,rate,stage,c0=None,step=300.):
        p=self.p;J=p.current_density(rate)*(1 if stage=='discharge' else -1);c=np.full((self.n,self.m),.15 if stage=='discharge' else .80) if c0 is None else c0.copy()
        def rhs(t,y):
            z=y.reshape(c.shape);_,q,_,_=self.fields(z,J);return (z@self.L.T+q[:,None]*self.b).ravel()
        def voltage(t,y):
            v,_,_,_=self.fields(y.reshape(c.shape),J);return v-p.low if J>0 else p.high-v
        def bounds(t,y):
            z=y.reshape(c.shape);_,_,surf,_=self.fields(z,J);return min(z.min(),1-z.max(),surf.min(),1-surf.max())
        for e in (voltage,bounds):e.terminal=True;e.direction=-1
        if min(voltage(0,c.ravel()),bounds(0,c.ravel()))<=0:raise ValueError('initial condition outside operating window')
        sol=solve_ivp(rhs,(0,rate*3600*2),c.ravel(),method='BDF',max_step=step,rtol=1e-7,atol=1e-9,events=[voltage,bounds],dense_output=True)
        if not sol.success:raise RuntimeError(sol.message)
        t=np.linspace(0,sol.t[-1],101);z=sol.sol(t).T.reshape((-1,*c.shape));fs=[self.fields(v,J) for v in z];v=np.array([f[0] for f in fs]);mean=(z@self.w).mean(axis=1);q=abs(J)*p.A*t[-1]/3.6/p.mass_g
        mass=float(np.max(abs((mean-mean[0])*p.F*p.cmax*p.eps*p.L-J*t)))
        return dict(rate=rate,stage=stage,capacity=q,end_s=float(t[-1]),termination='voltage' if len(sol.t_events[0]) else 'occupancy' if len(sol.t_events[1]) else 'horizon',mass_residual_C_m2=mass,algebraic_residual=max(f[3] for f in fs),min_theta=float(min(z.min(),min(f[2].min() for f in fs))),max_theta=float(max(z.max(),max(f[2].max() for f in fs))),time_s=t.tolist(),voltage=v.tolist()),z[-1]

def run():
    p=Params();rows=[]
    for nx,nr,step in [(4,12,300.),(8,24,150.)]:
        s=Solver(p,nx,nr)
        for rate in (20,10,5):
            for stage in ('charge','discharge'):
                d,_=s.stage(rate,stage,step=step);d.update(mesh=[nx,nr],step=step);rows.append(d)
                print(nx,nr,rate,stage,d['capacity'],d['termination'],flush=True)
    return dict(scope='synthetic independent uniform-start stages; no paper calibration or degradation',params=asdict(p),rows=rows)
if __name__=='__main__':
    from pathlib import Path
    Path('foundation_result.json').write_text(json.dumps(run(),indent=2,allow_nan=False)+'\n')
