"""Matched-count follow-up using the same synthetic ground truth and methods."""
import json,sys,time
import numpy as np
import torch
from inverse_interface import P,K,grid,voltage,state,ls,fit,jac_ratio

def run():
    torch.set_num_threads(1)
    t=np.repeat(np.arange(30.),2);amps=np.tile([.25,.5,1.,2.,4.],6);j=(amps[:,None]*np.array([-1.,1.])).ravel()
    te,je=grid(np.arange(30.,51.),[1.5,3.]);ytest=voltage(te,je,P);rows=[]
    for noise in (0.,1.,5.):
        for seed in (11,23):
            y=voltage(t,j,P)+np.random.default_rng(seed).normal(0,noise,len(t))
            for method in ('LS','PINN'):
                start=time.monotonic()
                if method=='LS':
                    p=ls(t,j,y);pred=voltage(te,je,p)
                else:
                    m=fit(t,j,y,seed);p=m.params().detach().numpy()
                    with torch.no_grad():pred=m(torch.tensor(te[:,None]/50),torch.tensor(je[:,None])).numpy().ravel()
                row=dict(noise_mv=noise,seed=seed,method=method,params=p.tolist(),error_pct=(100*abs(p/P-1)).tolist(),test_rmse_mv=float(np.sqrt(np.mean((pred-ytest)**2))),seconds=time.monotonic()-start)
                rows.append(row);print(row,flush=True)
    return dict(n=len(t),jac_ratio=jac_ratio(t,j),metrics=rows)
if __name__=='__main__':
    with open(sys.argv[1],'w') as f:json.dump(run(),f,indent=2)
