"""Paper-constrained constant-D P1 FEM diagnostic, no new parameter fitting."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from scipy.linalg import solve
from scipy.optimize import root
from scipy.interpolate import PchipInterpolator
from scipy.integrate import solve_ivp
F,R,T,C,L,S,P,A=96487.,8.314,323.15,47664.,40e-6,725e-6,10e-6,2.83e-5
M=5e-3*A*1e4; Q=165*M/1000

def inventory(eps):return F*C*L*A*eps/3600*1000/M

def matrices(n,spherical=False):
    x=np.linspace(0,1,n+1);m=np.zeros((n+1,n+1));k=m.copy();z,w=np.polynomial.legendre.leggauss(3)
    for i in range(n):
        h=x[i+1]-x[i]
        for q,wt in zip(z,w):
            t=(q+1)/2;b=np.array([1-t,t]);d=np.array([-1.,1.])/h;f=wt*h/2*((x[i]+t*h)**2 if spherical else 1.)
            m[i:i+2,i:i+2]+=f*np.outer(b,b);k[i:i+2,i:i+2]+=f*np.outer(d,d)
    return m,k

class PaperFEM:
    def __init__(self,u,eps,phase,j0,nx=4,nr=10):
        self.eps=eps;self.u=u;self.j0=j0;self.aL=3*eps/P*L;self.beta=F/(2*R*T);self.shape=(nx+1,nr+1)
        m,k=matrices(nx);mr,kr=matrices(nr,True);self.wx=m.sum(0);self.wr=3*mr.sum(0)
        e=np.zeros_like(m);s=e.copy();ke=k*.43*phase**1.5/L;ks=k*.17*phase**1.5/L
        e[1:]=solve(ke[1:,1:],-self.aL*m[1:],assume_a='pos');s[:-1]=solve(ks[:-1,:-1],self.aL*m[:-1],assume_a='pos');self.delta=s-e
        self.radial=solve(mr,-kr,assume_a='pos')*2e-13/P**2;end=np.zeros(nr+1);end[-1]=1;self.flux=solve(mr,end,assume_a='pos')/(F*P*C)
    def fields(self,theta,I,stage):
        J=I/A;u=self.u[stage](np.clip(1-theta,0,1));left=-np.arcsinh(J/200)/self.beta-J*S/.43;n=len(theta);j0=self.j0
        def res(z):
            j=z[:n];return np.r_[z[-1]-left+self.delta@j-u+np.arcsinh(j/(2*j0))/self.beta,self.wx@j-J/self.aL]
        def jac(z):return np.block([[self.delta+np.diag(1/(self.beta*np.sqrt((2*j0)**2+z[:n]**2))),np.ones((n,1))],[self.wx[None,:],np.zeros((1,1))]])
        z=root(res,np.r_[np.full(n,J/self.aL),u.mean()+left],jac=jac,tol=1e-10)
        if not np.isfinite(z.x).all() or np.max(abs(res(z.x)))>1e-8:raise RuntimeError('axial residual')
        return z.x[-1],z.x[:n]
    def stage(self,stage,rate,c0=None,*,max_step=120,rtol=1e-7,atol=1e-9,output_step=30):
        if not all(np.isfinite(v) and v>0 for v in (max_step,rtol,atol,output_step)):raise ValueError("solver options must be finite and positive")
        if c0 is not None and np.shape(c0)!=self.shape:raise ValueError("initial state shape mismatch")
        I=Q/rate*(-1 if stage=='charge' else 1);c=np.ones(self.shape) if c0 is None else c0.copy()
        def rhs(t,y):
            z=y.reshape(self.shape);j=self.fields(z[:,-1],I,stage)[1];return (z@self.radial.T+j[:,None]*self.flux).ravel()
        def voltage(t,y):
            v=self.fields(y.reshape(self.shape)[:,-1],I,stage)[0];return 4.2-v if stage=='charge' else v-2.7
        def occ(t,y):return y.min() if stage=='charge' else 1-y.max()
        for e in (voltage,occ):e.terminal=True;e.direction=-1
        if voltage(0,c.ravel())<=0 or occ(0,c.ravel())<=0:raise RuntimeError('initial stage outside bounds')
        sol=solve_ivp(rhs,(0,rate*1.5*3600),c.ravel(),method='BDF',rtol=rtol,atol=atol,max_step=max_step,events=[voltage,occ],dense_output=True)
        if not sol.success:raise RuntimeError(sol.message)
        t=np.r_[np.arange(0,sol.t[-1],output_step),sol.t[-1]];z=sol.sol(t).T.reshape((-1,*self.shape));v=np.array([self.fields(s[:,-1],I,stage)[0] for s in z]);q=t[-1]/3600*abs(I)*1000/M
        dm=(self.wx@z[-1]@self.wr-self.wx@c@self.wr)*inventory(self.eps);expected=q*(-1 if stage=='charge' else 1)
        return pd.DataFrame(dict(time_h=t/3600,voltage_v=v)),z[-1],dict(capacity_mah_g=q,termination='voltage' if len(sol.t_events[0]) else 'occupancy' if len(sol.t_events[1]) else 'horizon',final_voltage_v=v[-1],mass_error_mah_g=abs(dm-expected))

def split_ref(path):
    t,v=pd.read_csv(path).to_numpy(float).T;k=int(v.argmax());out={}
    for stage,sl,t0 in [('charge',slice(None,k+1),t[0]),('discharge',slice(k+1,None),t[k])]:
        out[stage]=pd.DataFrame(dict(time_h=t[sl]-t0,voltage_v=v[sl])).groupby('time_h',as_index=False).mean()
    return out

def metrics(pred,ref,rate):
    t=ref.time_h.to_numpy();start=max(t[0],pred.time_h.iloc[0],1/60);end=min(t[-1],pred.time_h.iloc[-1]);q=np.linspace(start,end,1000);e=np.interp(q,pred.time_h,pred.voltage_v)-np.interp(q,t,ref.voltage_v)
    return dict(rmse_mv=1000*np.sqrt(np.mean(e**2)),reference_capacity_mah_g=165*t[-1]/rate,coverage_pct=100*end/t[-1])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input_dir');p.add_argument('--outdir',default='outputs/v072');a=p.parse_args();base=Path(a.input_dir);dest=Path(a.outdir);dest.mkdir(exist_ok=True,parents=True);u={}
    for stage in ('charge','discharge'):
        x,y=pd.read_csv(base/'SOLiD-PINN-OCV-Figure4'/f'ocv_{stage}_digitized.csv').to_numpy(float).T;u[stage]=PchipInterpolator(x,y)
    rows=[]
    for name,eps,phase,j0 in [('literal_0131',.131,.131,6.59173895),('inventory_derived',Q*3600/(F*C*L*A),.131,6.59173895),('historical_kinetics',Q*3600/(F*C*L*A),.131,.0566011934)]:
        for rate in (20,10,5):
            m=PaperFEM(u,eps,phase,j0);c=None;ref=split_ref(base/f'Ref_data_at_C{rate}.csv')
            for stage in ('charge','discharge'):
                try:
                    pred,c,d=m.stage(stage,rate,c);row=dict(case=name,rate=rate,stage=stage,eps=eps,phase=phase,j0=j0,**d,**metrics(pred,ref[stage],rate));row['capacity_error_pct']=100*(row['capacity_mah_g']/row['reference_capacity_mah_g']-1);rows.append(row);print(row,flush=True);pred.to_csv(dest/f'{name}_{rate}_{stage}.csv',index=False)
                except RuntimeError as e:print('FAILED',name,rate,stage,str(e),flush=True);rows.append(dict(case=name,rate=rate,stage=stage,termination='failure: '+str(e)));break
            pd.DataFrame(rows).to_csv(dest/'metrics.csv',index=False)
if __name__=='__main__':main()
