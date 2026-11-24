"""Independent cross-solver benchmark, illustrative OCV only (not experiment)."""
import argparse
from dataclasses import replace
from pathlib import Path
import time
import numpy as np
import pandas as pd
from solid_pinn.numerical import ReducedP2D
from solid_pinn.parameters import Parameters
from solid_pinn.reference_fem import ReferenceFEM


def benchmark(nx_fem=6,nr_fem=10,nx_fvm=12,nr_fvm=20,dt=150.,rates=(20,10,5)):
    p=replace(Parameters(),exchange_current_cathode_a_m2=.0566011934,initial_soc=.0770454572)
    fem=ReferenceFEM(p,nx_fem,nr_fem)
    fvm=ReducedP2D(p,nx_fvm,nr_fvm)
    rows=[]
    for rate in rates:
        c0=d0=None
        for stage in ('charge','discharge'):
            I=p.current_a(rate)*(-1 if stage=='charge' else 1)
            J=I/p.area_m2
            start=time.perf_counter()
            t,c=fem.stage(stage,rate,c0,max_step=dt)
            c0=c[-1]
            fields=[fem.fields(k[:,-1],I,stage) for k in c]
            v=np.array([f.voltage for f in fields])
            fem_runtime=time.perf_counter()-start
            start=time.perf_counter()
            d,d0=fvm.simulate_stage(stage,d0,rate,dt_s=dt)
            fvm_runtime=time.perf_counter()-start
            tf=d.time_h.to_numpy()*3600; vf=d.voltage_v.to_numpy()
            end=min(t[-1],tf[-1]); tt=np.linspace(0,end,501)
            if end<=0 or t[-1]<=0: raise RuntimeError('no common stage duration')
            rmse=1000*np.sqrt(np.mean((np.interp(tt,t,v)-np.interp(tt,tf,vf))**2))
            cap=100*(tf[-1]-t[-1])/t[-1]
            fem_soc=np.array([fem.soc(k) for k in c]); fvm_soc=d.cell_soc.to_numpy()
            mass_fem=100*np.max(np.abs(fem_soc-(fem_soc[0]-I*t/(3600*p.nominal_capacity_ah))))
            mass_fvm=100*np.max(np.abs(fvm_soc-(fvm_soc[0]-I*tf/(3600*p.nominal_capacity_ah))))
            cur_fem=100*max(abs(fem.aL*(fem.wx@f.reaction)-J) for f in fields)/abs(J)
            f=fvm.solve_potentials(d0[:,-1],I,stage)
            cur_fvm=100*abs(p.active_surface_area_m_inv*fvm.dx*sum(f.reaction_current_a_m2)-J)/abs(J)
            xmid=(np.arange(nx_fvm)+.5)/nx_fvm
            ref=fields[-1]
            pe=1000*np.max(np.abs(np.interp(xmid,fem.x,ref.electrolyte)-f.electrolyte_potential_v))
            ps=1000*np.max(np.abs(np.interp(xmid,fem.x,ref.solid)-f.solid_potential_v))
            j=100*np.max(np.abs(np.interp(xmid,fem.x,ref.reaction)-f.reaction_current_a_m2))/abs(J/fem.aL)
            rows.append(dict(rate=rate,stage=stage,nx_fem=nx_fem,nr_fem=nr_fem,nx_fvm=nx_fvm,nr_fvm=nr_fvm,dt_s=dt,voltage_rmse_mv=rmse,capacity_difference_pct=cap,mass_fem_pct_nominal=mass_fem,mass_fvm_pct_nominal=mass_fvm,current_fem_max_pct=cur_fem,current_fvm_final_pct=cur_fvm,final_electrolyte_max_mv=pe,final_solid_max_mv=ps,final_reaction_max_pct_mean=j,fem_runtime_s=fem_runtime,fvm_runtime_s=fvm_runtime))
    return pd.DataFrame(rows)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',default='outputs/fem_verification.csv'); parser.add_argument('--dt',type=float,default=150)
    parser.add_argument('--nx-fem',type=int,default=6); parser.add_argument('--nr-fem',type=int,default=10)
    parser.add_argument('--nx-fvm',type=int,default=12); parser.add_argument('--nr-fvm',type=int,default=20)
    a=parser.parse_args(); result=benchmark(a.nx_fem,a.nr_fem,a.nx_fvm,a.nr_fvm,a.dt)
    path=Path(a.out); path.parent.mkdir(parents=True,exist_ok=True); result.to_csv(path,index=False); print(result.to_string(index=False))
