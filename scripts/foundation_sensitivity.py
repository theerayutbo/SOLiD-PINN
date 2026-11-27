"""Local log-parameter sensitivity; synthetic discharge, not parameter recovery."""
from dataclasses import replace
from pathlib import Path
import json
import numpy as np
from scipy.integrate import solve_ivp
from canonical_fv import Params,Solver

NAMES=('D','ksep','kcat','scat','j0','jli')
RATES=(20,10,5)

def sample(p,rate,times,nx=4,nr=12):
    s=Solver(p,nx,nr);c=np.full((nx,nr),.15);J=p.current_density(rate)
    def rhs(t,y):
        z=y.reshape(c.shape);_,q,_,_=s.fields(z,J)
        return (z@s.L.T+q[:,None]*s.b).ravel()
    sol=solve_ivp(rhs,(0,float(times[-1])),c.ravel(),method='BDF',max_step=300.,rtol=1e-8,atol=1e-10,t_eval=times)
    if not sol.success:raise RuntimeError(sol.message)
    vals=[]
    for y in sol.y.T:
        z=y.reshape(c.shape);v,_,surf,_=s.fields(z,J)
        if min(z.min(),surf.min())<=0 or max(z.max(),surf.max())>=1 or v<=p.low:raise RuntimeError('outside valid pre-cutoff window')
        vals.append(v)
    return np.array(vals)

def run():
    p=Params();s=Solver(p);times={r:np.linspace(0,.85*s.stage(r,'discharge')[0]['end_s'],81) for r in RATES}
    js={};spectra={}
    for h in (.005,.0025):
        blocks=[]
        for r in RATES:
            cols=[]
            for name in NAMES:
                value=getattr(p,name)
                hi=sample(replace(p,**{name:value*np.exp(h)}),r,times[r]);lo=sample(replace(p,**{name:value*np.exp(-h)}),r,times[r]);cols.append((hi-lo)/(2*h*.005))
            blocks.append(np.column_stack(cols))
        js[h]=blocks
        for label,J in [('C20',blocks[0]),('all',np.vstack(blocks))]:
            _,v,vt=np.linalg.svd(J,full_matrices=False);spectra[f'{h}:{label}']=dict(singular_values=v.tolist(),condition=float(v[0]/v[-1]),weak_direction=vt[-1].tolist(),column_norms=np.linalg.norm(J,axis=0).tolist())
    return dict(scope='synthetic local voltage sensitivity only, 5 mV independent noise assumed, no inverse fitting',parameters=NAMES,rates=RATES,spectra=spectra,relative_jacobian_step_difference=float(np.linalg.norm(np.vstack(js[.005])-np.vstack(js[.0025]))/np.linalg.norm(np.vstack(js[.0025]))))

if __name__=='__main__':
    d=run();Path('foundation_sensitivity.json').write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');print(json.dumps(d,indent=2))
