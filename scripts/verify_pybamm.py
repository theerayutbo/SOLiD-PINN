"""Compare custom PyBaMM DAE and original FVM on matched uniform-start stages."""
import argparse
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
from solid_pinn.parameters import Parameters
from solid_pinn.numerical import ReducedP2D
from solid_pinn.reference_pybamm import solve_stage


def benchmark(nx=12,nr=20,dt=30.,rates=(20,10,5)):
    rows=[]
    for rate in rates:
        for stage,soc0 in (("charge",.0770454572),("discharge",.90)):
            p=replace(Parameters(),initial_soc=soc0,exchange_current_cathode_a_m2=.0566011934)
            sol=solve_stage(p,stage,rate,nx,nr,dt)
            t=sol.t
            v=np.asarray(sol["Voltage [V]"].entries).ravel()
            soc=np.asarray(sol["SOC"].entries).ravel()
            j=np.asarray(sol["Integrated reaction current [A/m2]"].entries).ravel()
            fvm=ReducedP2D(p,nx,nr)
            f,_=fvm.simulate_stage(stage,c_rate_denominator=rate,dt_s=dt)
            tf=f.time_h.to_numpy()*3600
            end=min(t[-1],tf[-1])
            if end<=0: raise RuntimeError("no common time interval")
            tt=np.linspace(0,end,501)
            I=p.current_a(rate)*(-1 if stage=="charge" else 1)
            J=I/p.area_m2
            rmse=1000*np.sqrt(np.mean((np.interp(tt,t,v)-np.interp(tt,tf,f.voltage_v))**2))
            rows.append(dict(rate=rate,stage=stage,initial_soc=soc0,nx=nx,nr=nr,dt_s=dt,
                voltage_rmse_mv=rmse,capacity_difference_pct=100*(tf[-1]-t[-1])/t[-1],
                mass_pybamm_pct_nominal=100*np.max(abs(soc-(soc0-I*t/(3600*p.nominal_capacity_ah)))),
                current_pybamm_max_pct=100*np.max(abs(j-J))/abs(J),
                termination=str(sol.termination)))
    return pd.DataFrame(rows)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",default="outputs/pybamm_verification.csv")
    parser.add_argument("--dt",type=float,default=30.)
    parser.add_argument("--nx",type=int,default=12)
    parser.add_argument("--nr",type=int,default=20)
    a=parser.parse_args()
    result=benchmark(a.nx,a.nr,a.dt)
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    result.to_csv(dest,index=False);print(result.to_string(index=False))
