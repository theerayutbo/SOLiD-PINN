"""Matched uniform-start PyBaMM/FEM/FVM benchmark; no experimental data.
All three use identical physical parameters, stage OCV, applied current and
cutoff thresholds. Spatial discretisations and surface reconstruction differ.
"""
import argparse
from dataclasses import replace
from pathlib import Path
from itertools import combinations
import time
import json
import numpy as np
import pandas as pd
from solid_pinn.parameters import Parameters
from solid_pinn.numerical import ReducedP2D
from solid_pinn.reference_fem import ReferenceFEM
from solid_pinn.reference_pybamm import solve_stage


def benchmark(nx=12,nr=20,dt=30.,rates=(20,10,5)):
    rows=[]
    for rate in rates:
        for stage,soc0 in (("charge",.0770454572),("discharge",.90)):
            p=replace(Parameters(),initial_soc=soc0,exchange_current_cathode_a_m2=.0566011934)
            I=p.current_a(rate)*(-1 if stage=="charge" else 1)
            J=I/p.area_m2
            start=time.perf_counter()
            sol=solve_stage(p,stage,rate,nx,nr,dt)
            pb_time=time.perf_counter()-start
            t=np.asarray(sol.t).ravel()
            v=np.asarray(sol["Voltage [V]"].entries).ravel()
            soc=np.asarray(sol["SOC"].entries).ravel()
            j=np.asarray(sol["Integrated reaction current [A/m2]"].entries).ravel()
            fem=ReferenceFEM(p,nx,nr)
            start=time.perf_counter()
            te,ce=fem.stage(stage,rate,max_step=dt)
            fields=[fem.fields(c[:,-1],I,stage) for c in ce]
            ve=np.array([f.voltage for f in fields])
            se=np.array([fem.soc(c) for c in ce])
            je=np.array([fem.aL*(fem.wx@f.reaction) for f in fields])
            fem_time=time.perf_counter()-start
            fvm=ReducedP2D(p,nx,nr)
            start=time.perf_counter()
            f,cf=fvm.simulate_stage(stage,c_rate_denominator=rate,dt_s=dt)
            fvm_time=time.perf_counter()-start
            tf=f.time_h.to_numpy()*3600
            ffinal=fvm.solve_potentials(cf[:,-1],I,stage)
            jf=np.array([p.active_surface_area_m_inv*fvm.dx*sum(ffinal.reaction_current_a_m2)])
            series={"PyBaMM":(t,v,soc,j,pb_time),"FEM":(te,ve,se,je,fem_time),
                    "FVM":(tf,f.voltage_v.to_numpy(),f.cell_soc.to_numpy(),jf,fvm_time)}
            end=min(z[0][-1] for z in series.values())
            if end<=0: raise RuntimeError("no common time interval")
            tt=np.linspace(0,end,2001)
            for name,(times,volts,state,reaction,runtime) in series.items():
                if not np.isfinite(np.r_[times,volts,state,reaction]).all() or np.any(np.diff(times)<=0):
                    raise RuntimeError(f"invalid {name} solution")
                if len(times)!=len(volts) or len(times)!=len(state):
                    raise RuntimeError(f"invalid {name} output sizes")
                # Distinguish a real terminal cutoff from horizon truncation.
                margin=min(p.upper_cutoff_v-volts[-1],.995-state[-1]) if stage=="charge" else min(volts[-1]-p.lower_cutoff_v,state[-1]-.005)
                rows.append(dict(benchmark_id="v061_sigma017",sigma_cathode_s_m=p.sigma_cathode_s_m,kind="solver",rate=rate,stage=stage,solver=name,other="",
                    initial_soc=soc0,nx=nx,nr=nr,dt_s=dt,end_s=times[-1],
                    capacity_mah=abs(I)*times[-1]/3.6,
                    final_voltage_v=volts[-1],final_soc=state[-1],
                    cutoff_reached=bool(abs(margin)<1e-4),
                    mass_balance_pct_nominal=100*np.max(abs(state-(soc0-I*times/(3600*p.nominal_capacity_ah)))),
                    current_balance_pct=100*np.max(abs(reaction-J))/abs(J),
                    current_scope="final" if name=="FVM" else "sampled",
                    runtime_s=runtime,termination=str(sol.termination) if name=="PyBaMM" else "see cutoff_reached"))
            for a,b in combinations(series,2):
                ta,va,*_=series[a];tb,vb,*_=series[b]
                err=np.interp(tt,ta,va)-np.interp(tt,tb,vb)
                rows.append(dict(benchmark_id="v061_sigma017",sigma_cathode_s_m=p.sigma_cathode_s_m,kind="pair",rate=rate,stage=stage,solver=a,other=b,
                    initial_soc=soc0,nx=nx,nr=nr,dt_s=dt,common_end_s=end,
                    common_coverage_pct=100*end/max(ta[-1],tb[-1]),
                    voltage_rmse_mv=1000*np.sqrt(np.mean(err**2)),
                    voltage_max_abs_mv=1000*np.max(abs(err)),
                    capacity_difference_pct=100*abs(ta[-1]-tb[-1])/ta[-1]))
            print(json.dumps([r for r in rows if r["rate"]==rate and r["stage"]==stage],default=float),flush=True)
    return pd.DataFrame(rows)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",default="outputs/v061_three_solver_matched.csv")
    parser.add_argument("--dt",type=float,default=30.)
    parser.add_argument("--nx",type=int,default=12)
    parser.add_argument("--nr",type=int,default=20)
    a=parser.parse_args()
    result=benchmark(a.nx,a.nr,a.dt)
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    result.to_csv(dest,index=False)
    print("MATCHED BENCHMARK CSV BEGIN")
    print(result.to_csv(index=False),end="")
    print("MATCHED BENCHMARK CSV END")
