"""Matched sequential cycles and independent spatial/time refinement.
No fitting. Physical-time comparison, no curve alignment by SOC or capacity.
"""
from dataclasses import asdict
from pathlib import Path
import json
import numpy as np
from scipy.integrate import solve_ivp
from canonical_fv import Params,Solver
from foundation_fem import FEM

CONFIGS=(('coarse',4,12,300.,1e-7),('axial',8,12,300.,1e-7),('radial',8,24,300.,1e-7),('time',8,24,150.,1e-8),('fine',16,48,150.,1e-8))

def stage(s,c,rate,kind,step,rtol):
    p=s.p;J=p.current_density(rate)*{'charge':-1,'rest':0,'discharge':1}[kind]
    fem=isinstance(s,FEM);mean=s.mean if fem else lambda z:float((z@s.w).mean())
    def rhs(t,y):
        z=y.reshape(c.shape);_,q,_,_=s.fields(z,J)
        return (s.rhs(z,q) if fem else z@s.L.T+q[:,None]*s.b).ravel()
    def voltage(t,y):
        v=s.fields(y.reshape(c.shape),J)[0];return v-p.low if J>0 else p.high-v
    def bounds(t,y):
        z=y.reshape(c.shape);surf=s.fields(z,J)[2];return min(z.min(),1-z.max(),surf.min(),1-surf.max())
    for e in (voltage,bounds):e.terminal=True;e.direction=-1
    events=[bounds] if kind=='rest' else [voltage,bounds]
    if any(e(0,c.ravel())<=0 for e in events):raise RuntimeError('invalid initial state')
    horizon=1800. if kind=='rest' else 2*rate*3600.
    sol=solve_ivp(rhs,(0,horizon),c.ravel(),method='BDF',max_step=step,rtol=rtol,atol=rtol*.01,events=events,dense_output=True)
    if not sol.success:raise RuntimeError(sol.message)
    t=np.linspace(0,sol.t[-1],201);states=sol.sol(t).T.reshape((-1,*c.shape));fields=[s.fields(z,J) for z in states]
    m=np.array([mean(z) for z in states]);v=np.array([f[0] for f in fields]);surfs=np.array([f[2] for f in fields]);qs=np.array([f[1] for f in fields]);weights=s.wx if fem else np.full(s.n,s.dx)
    # Compare same geometric positions via piecewise linear reconstruction.
    x=s.x if fem else (np.arange(s.n)+.5)*s.dx
    probe=np.linspace(.125,.875,7)*p.L
    sp=np.array([np.interp(probe,x,f) for f in surfs]);jp=np.array([np.interp(probe,x,f/weights) for f in qs])
    why=('rest_complete' if kind=='rest' and sol.status==0 else 'voltage' if kind!='rest' and len(sol.t_events[0]) else 'occupancy' if sol.status==1 else 'horizon')
    row=dict(stage=kind,rate=rate,termination=why,end_s=float(t[-1]),capacity=float(abs(J)*p.A*t[-1]/(3.6*p.mass_g)),current_density=float(J),start_mean=float(m[0]),end_mean=float(m[-1]),mass_residual=float(max(abs((m-m[0])*p.F*p.cmax*p.eps*p.L-J*t))),algebraic_residual=float(max(f[3] for f in fields)),min_theta=float(min(states.min(),surfs.min())),max_theta=float(max(states.max(),surfs.max())),time_s=t.tolist(),voltage=v.tolist(),mean_theta=m.tolist(),surface_probes=sp.tolist(),reaction_density_probes=jp.tolist())
    return row,states[-1]

def cycle(s,rate,step,rtol):
    c=np.full((s.n,s.m),.8);rows=[]
    for kind in ('charge','rest','discharge'):
        d,c=stage(s,c,rate,kind,step,rtol);rows.append(d)
    return rows

def compare(a,b):
    t=np.linspace(0,min(a['end_s'],b['end_s']),201)
    def delta(key):
        u=np.asarray(a[key]);v=np.asarray(b[key]);u=u[:,None] if u.ndim==1 else u;v=v[:,None] if v.ndim==1 else v
        return np.column_stack([np.interp(t,a['time_s'],u[:,k])-np.interp(t,b['time_s'],v[:,k]) for k in range(u.shape[1])])
    v=delta('voltage')*1000;surface=delta('surface_probes');reaction=delta('reaction_density_probes')
    return dict(max_voltage_mv=float(np.max(abs(v))),voltage_rmse_mv=float(np.sqrt(np.mean(v*v))),capacity_delta_pct=0. if b['capacity']==0 else 100*abs(a['capacity']/b['capacity']-1),time_delta_s=abs(a['end_s']-b['end_s']),surface_max=float(np.max(abs(surface))),reaction_rmse_A_m3=float(np.sqrt(np.mean(reaction*reaction))))

def run(configs=CONFIGS,rates=(20,10,5)):
    p=Params();rows=[];lookup={};pairs=[]
    for label,nx,nr,step,rtol in configs:
        for name,cls in [('FVM',Solver),('FEM',FEM)]:
            s=cls(p,nx,nr)
            for rate in rates:
                for d in cycle(s,rate,step,rtol):
                    d.update(solver=name,config=label,mesh=[nx,nr],step=step,rtol=rtol);rows.append(d);lookup[name,label,rate,d['stage']]=d
                print(label,name,rate,flush=True)
    labels=[x[0] for x in configs]
    for rate in rates:
        for kind in ('charge','rest','discharge'):
            for name in ('FVM','FEM'):
                for a,b in zip(labels[:-1],labels[1:]):
                    pairs.append(dict(kind='refinement',solver=name,comparison=a+'->'+b,rate=rate,stage=kind,**compare(lookup[name,a,rate,kind],lookup[name,b,rate,kind])))
            for label in labels:
                pairs.append(dict(kind='cross_solver',comparison=label,rate=rate,stage=kind,**compare(lookup['FVM',label,rate,kind],lookup['FEM',label,rate,kind])))
    physical=all(x['termination']==('rest_complete' if x['stage']=='rest' else 'voltage') and x['mass_residual']<1e-5 and x['algebraic_residual']<1e-8 and 0<x['min_theta']<=x['max_theta']<1 for x in rows)
    continuity=all(abs(lookup[n,l,r,a]['end_mean']-lookup[n,l,r,b]['start_mean'])<1e-12 for n in ('FVM','FEM') for l in labels for r in rates for a,b in [('charge','rest'),('rest','discharge')])
    final=[x for x in pairs if x['kind']=='cross_solver' and x['comparison']==labels[-1]]
    return dict(scope='synthetic matched sequential charge/rest/discharge; independent spatial discretizations; shared BDF integrator',params=asdict(p),rows=rows,pairs=pairs,physical_gate=physical,continuity_gate=continuity,cross_solver_gate=all(x['max_voltage_mv']<=1 and x['capacity_delta_pct']<=.5 for x in final))

if __name__=='__main__':
    Path('foundation_verification.json').write_text(json.dumps(run(),indent=2,allow_nan=False)+'\n')
