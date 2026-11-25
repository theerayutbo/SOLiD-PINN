"""Synthetic symmetric-cell inverse benchmark, not experimental calibration."""
import json, sys, time, platform
import numpy as np
import scipy
from scipy.optimize import least_squares
import torch
from torch import nn
P=np.array([25.,12.,15.,.8]); LO=np.array([1.,1.,2.,.1]); HI=np.array([60.,60.,80.,5.])
K=4*8.314*298.15/96485*1000

def state(t,p): return p[1]+(p[0]-p[1])*np.exp(-t/p[2])
def voltage(t,j,p): return 2*j*state(t,p)+K*np.arcsinh(j/(2*p[3]))
def grid(t,a):
    t,j=np.meshgrid(t,np.r_[-np.array(a),a],indexing='ij');return t.ravel(),j.ravel()

def ls(t,j,y):
    fits=[least_squares(lambda p:voltage(t,j,p)-y,x,bounds=(LO,HI),x_scale='jac') for x in ([20,10,10,.5],[35,20,30,2],[10,5,5,.3])]
    return min((f for f in fits if f.success),key=lambda f:f.cost).x

class PINN(nn.Module):
    def __init__(self):
        super().__init__();x=np.array([20.,10.,10.,.5]);self.raw=nn.Parameter(torch.tensor(np.log((x-LO)/(HI-x))))
        self.net=nn.Sequential(nn.Linear(1,16),nn.Tanh(),nn.Linear(16,16),nn.Tanh(),nn.Linear(16,1));self.register_buffer('lo',torch.tensor(LO));self.register_buffer('hi',torch.tensor(HI))
    def params(self):return self.lo+(self.hi-self.lo)*torch.sigmoid(self.raw)
    def state(self,x):return self.params()[0]*torch.exp(x*self.net(x))
    def forward(self,x,j):return 2*j*self.state(x)+K*torch.asinh(j/(2*self.params()[3]))
    def residual(self,x):
        r=self.state(x)/20;dr=torch.autograd.grad(r,x,torch.ones_like(r),create_graph=True)[0];return dr+50/self.params()[2]*(r-self.params()[1]/20)

def fit(t,j,y,seed):
    torch.manual_seed(seed);m=PINN().double();x=torch.tensor(t[:,None]/50);j=torch.tensor(j[:,None]);y=torch.tensor(y[:,None]);xc=torch.linspace(0,1,101,dtype=torch.float64).reshape(-1,1).requires_grad_()
    def loss():return ((m(x,j)-y)/100).square().mean()+m.residual(xc).square().mean()
    opt=torch.optim.Adam(m.parameters(),lr=.01)
    for _ in range(400):
        opt.zero_grad();l=loss();l.backward();opt.step()
    opt=torch.optim.LBFGS(m.parameters(),max_iter=250,line_search_fn='strong_wolfe',tolerance_grad=1e-10,tolerance_change=1e-12)
    def closure():
        opt.zero_grad();l=loss();l.backward();return l
    opt.step(closure);return m

def jac_ratio(t,j):
    cols=[]
    for k in range(4):
        a=P.copy();b=P.copy();a[k]*=np.exp(1e-5);b[k]*=np.exp(-1e-5);cols.append((voltage(t,j,a)-voltage(t,j,b))/2e-5)
    s=np.linalg.svd(np.column_stack(cols),compute_uv=False);return float(s[-1]/s[0])

def run():
    torch.set_num_threads(1);rows=[];diag=[];te,je=grid(np.arange(30.,51.),[1.5,3.]);target=voltage(te,je,P)
    for design,amps in [('single',[1.]),('multi',[.25,.5,1.,2.,4.])]:
        t,j=grid(np.arange(30.),amps);v=voltage(t,j,P);diag.append(dict(design=design,n=len(t),jac_ratio=jac_ratio(t,j)))
        for noise in (0.,1.,5.):
            for seed in (11,23):
                y=v+np.random.default_rng(seed).normal(0,noise,len(t))
                for method in ('LS','PINN'):
                    start=time.monotonic()
                    if method=='LS':
                        p=ls(t,j,y);train=voltage(t,j,p);pred=voltage(te,je,p);rs=state(te,p);ode=0.
                    else:
                        m=fit(t,j,y,seed);p=m.params().detach().numpy()
                        with torch.no_grad():
                            train=m(torch.tensor(t[:,None]/50),torch.tensor(j[:,None])).numpy().ravel();pred=m(torch.tensor(te[:,None]/50),torch.tensor(je[:,None])).numpy().ravel();rs=m.state(torch.tensor(te[:,None]/50)).numpy().ravel()
                        xx=torch.linspace(0,1,201,dtype=torch.float64).reshape(-1,1).requires_grad_();ode=float(m.residual(xx).square().mean().sqrt().detach())
                    row=dict(design=design,noise_mv=noise,seed=seed,method=method,params=p.tolist(),error_pct=(100*abs(p/P-1)).tolist(),train_rmse_mv=float(np.sqrt(np.mean((train-y)**2))),test_rmse_mv=float(np.sqrt(np.mean((pred-target)**2))),state_rmse=float(np.sqrt(np.mean((rs-state(te,P))**2))),ode_rmse=ode,seconds=time.monotonic()-start)
                    if not np.isfinite(p).all() or not np.isfinite(pred).all():raise RuntimeError('nonfinite result')
                    rows.append(row);print(design,noise,seed,method,round(row['test_rmse_mv'],3),np.round(p,3),flush=True)
    return dict(truth=P.tolist(),units=['ohm cm2','ohm cm2','h','mA/cm2'],temperature_K=298.15,K_mv=K,train_h=[0,29],test_h=[30,50],test_amplitudes=[1.5,3],adam_steps=400,lbfgs_max_iter=250,environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,torch=torch.__version__),diagnostics=diag,metrics=rows)

if __name__=='__main__':
    with open(sys.argv[1],'w') as f:json.dump(run(),f,indent=2)
