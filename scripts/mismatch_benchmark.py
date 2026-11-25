"""Synthetic hidden-state benchmark; known observation map, unknown rate."""
import argparse,json,platform,time
from pathlib import Path
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares
import torch
from torch import nn
import torch.nn.functional as F
K=4*8.314*298.15/96485*1000
C=.06; GAIN=18.; J0=.8
TRAIN=np.array([.25,.75,1.5,3.]); TEST=np.array([.5,1.,2.,4.]); TIMES=np.arange(51.)
def true_rate(j): return .10*j*j/(1+.7*j*j)
def base(t,j): return 2*j*(12+13*np.exp(-t/15))+K*np.arcsinh(j/(2*J0))
def observe(t,j,x): return base(t,j)+2*j*GAIN*x
def truth(amps):
    a=true_rate(amps)
    return solve_ivp(lambda t,x:a*(1-x)-C*x**3,(0,50),np.zeros(len(amps)),t_eval=TIMES,rtol=1e-11,atol=1e-13).y.T

def rk4(amps,rate,steps=4):
    x=np.zeros(len(amps)); out=[x.copy()]; a=rate(amps);dt=1/steps
    def f(v):return a*(1-v)-C*v**3
    for _ in range(50):
        for _ in range(steps):
            k1=f(x);k2=f(x+dt*k1/2);k3=f(x+dt*k2/2);k4=f(x+dt*k3);x=x+dt*(k1+2*k2+2*k3+k4)/6
        out.append(x.copy())
    return np.array(out)

def rate_model(kind,p,j):
    if kind=='misspecified':return p[0]*j*j
    if kind=='oracle':return p[0]*j*j/(1+p[1]*j*j)
    return np.interp(j,np.r_[0,TRAIN,4.],np.r_[0,np.cumsum(p),np.sum(p)+p[-1]/1.5])

def numerical(kind,y):
    init={'misspecified':[.02],'oracle':[.08,.5],'flexible':[.005,.035,.035,.035]}[kind]
    upper={'misspecified':[.3],'oracle':[.3,2.],'flexible':[.3]*4}[kind]
    def residual(p):return (observe(TIMES[:30,None],TRAIN,rk4(TRAIN,lambda j:rate_model(kind,p,j))[:30])-y).ravel()
    fit=least_squares(residual,init,bounds=(np.full(len(init),1e-6),upper),max_nfev=250,xtol=1e-10,ftol=1e-10,gtol=1e-10)
    if not fit.success:raise RuntimeError(fit.message)
    return lambda j:rate_model(kind,fit.x,j),fit.x.tolist()

class Hybrid(nn.Module):
    def __init__(self):
        super().__init__();self.rate_net=nn.Sequential(nn.Linear(1,12),nn.Tanh(),nn.Linear(12,1));self.state_net=nn.Sequential(nn.Linear(2,24),nn.Tanh(),nn.Linear(24,24),nn.Tanh(),nn.Linear(24,1))
    def rate(self,j):return (j/4)**2*F.softplus(self.rate_net(j/4))
    def state(self,t,j):return -torch.expm1(-t/50*F.softplus(self.state_net(torch.cat((t/50,j/4),1))))
    def residual(self,t,j):
        x=self.state(t,j);dx=torch.autograd.grad(x,t,torch.ones_like(x),create_graph=True)[0]
        return 50*(dx-self.rate(j)*(1-x)+C*x**3)

def train_pinn(y,seed):
    torch.manual_seed(seed);m=Hybrid().double()
    def grid(t,j):
        a,b=np.meshgrid(t,j,indexing='ij');return torch.tensor(a.ravel()[:,None]),torch.tensor(b.ravel()[:,None])
    t,j=grid(TIMES[:30],TRAIN);yc=torch.tensor(y.ravel()[:,None]);bc=torch.tensor(base(TIMES[:30,None],TRAIN).ravel()[:,None]);tc,jc=grid(np.linspace(0,50,31),np.linspace(.25,4,11));tc.requires_grad_()
    def loss():return (((bc+2*j*GAIN*m.state(t,j)-yc)/50)**2).mean()+m.residual(tc,jc).square().mean()
    opt=torch.optim.Adam(m.parameters(),lr=.005)
    for _ in range(800):
        opt.zero_grad();tc.grad=None;l=loss();l.backward();opt.step()
    opt=torch.optim.LBFGS(m.parameters(),max_iter=200,line_search_fn='strong_wolfe',tolerance_grad=1e-10,tolerance_change=1e-12)
    def closure():
        opt.zero_grad();tc.grad=None;l=loss();l.backward();return l
    opt.step(closure)
    def rate(a):
        with torch.no_grad():return m.rate(torch.tensor(np.asarray(a)[:,None],dtype=torch.float64)).numpy().ravel()
    def state(a):
        t,j=grid(TIMES,a)
        with torch.no_grad():return m.state(t,j).numpy().reshape(len(TIMES),len(a))
    tv,jv=grid(np.linspace(.5,49.5,50),np.linspace(.35,3.95,13));tv.requires_grad_();res=float(m.residual(tv,jv).square().mean().sqrt().detach())
    return rate,state,res

def rmse(a,b):return float(np.sqrt(np.mean((a-b)**2)))
def run():
    torch.set_num_threads(1);xt=truth(TRAIN);xe=truth(TEST);yt=observe(TIMES[:,None],TRAIN,xt);ye=observe(TIMES[:,None],TEST,xe);rows=[]
    error=rmse(rk4(np.r_[TRAIN,TEST],true_rate),truth(np.r_[TRAIN,TEST]));assert error<1e-6
    for noise in (0.,1.,5.):
        for seed in (11,23):
            y=yt[:30]+np.random.default_rng(seed).normal(0,noise,yt[:30].shape)
            for kind in ('misspecified','oracle','flexible','hybrid_pinn'):
                start=time.monotonic();res=None;params=None
                if kind=='hybrid_pinn':rate,st,res=train_pinn(y,seed);a=st(TRAIN);b=st(TEST);b_solver=rk4(TEST,rate)
                else:rate,params=numerical(kind,y);a=rk4(TRAIN,rate);b=rk4(TEST,rate);b_solver=b
                va=observe(TIMES[:,None],TRAIN,a);vb=observe(TIMES[:,None],TEST,b)
                row=dict(method=kind,noise_mv=noise,seed=seed,train_rmse_mv=rmse(va[:30],y),seen_late_rmse_mv=rmse(va[30:],yt[30:]),unseen_interp_rmse_mv=rmse(vb[30:,:3],ye[30:,:3]),unseen_extra_rmse_mv=rmse(vb[30:,3],ye[30:,3]),latent_rmse=rmse(b[30:],xe[30:]),rate_rmse=rmse(rate(TEST),true_rate(TEST)),solver_state_gap=rmse(b,b_solver),ode_residual=res,params=params,seconds=time.monotonic()-start)
                if not all(np.isfinite(v) for v in row.values() if isinstance(v,float)):raise RuntimeError('nonfinite result')
                rows.append(row);print(kind,noise,seed,round(row['unseen_interp_rmse_mv'],3),round(row['unseen_extra_rmse_mv'],3),flush=True)
    return dict(scope='synthetic known observation map, unknown rate; not experimental validation',truth=dict(a=.1,b=.7,c=C,gain=GAIN,j0=J0),train_amplitudes=TRAIN.tolist(),test_amplitudes=TEST.tolist(),train_hours=[0,29],test_hours=[30,50],rk4_ground_truth_rmse=error,environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,torch=torch.__version__),metrics=rows)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();Path(a.out).write_text(json.dumps(run(),indent=2,allow_nan=False)+'\n')
