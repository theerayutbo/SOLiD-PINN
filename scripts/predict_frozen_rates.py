"""Frozen-parameter sequential C-rate predictions. No fitting."""
import argparse
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from solid_pinn.comsol_transfer import read_model, TransferFEM
from solid_pinn.transfer_fvm import TransferFVM


def run(path, outdir, nx=4, nr=10, max_step=120., rates=(20,10,5)):
    m=read_model(path); dest=Path(outdir);dest.mkdir(parents=True,exist_ok=True)
    rows=[];pairs=[]
    inventory=m['area']*m['L']*m['eps']*m['F']*m['cmax']/3600
    for rate in rates:
        solutions={}
        for label, cls in [('FEM',TransferFEM),('FVM',TransferFVM)]:
            s=cls(m,nx,nr);c=None
            for stage in ('charge','discharge'):
                d,c=s.stage(stage,rate,c,max_step=max_step)
                I=s.p.current_a(rate); signed=I*(-1 if stage=='charge' else 1)
                soc=d.cell_soc.to_numpy();t=d.time_h.to_numpy()
                j=s.fields(c[:,-1],signed,stage).reaction
                rows.append(dict(solver=label,rate=rate,stage=stage,nx=nx,nr=nr,max_step_s=max_step,
                    duration_h=t[-1],specific_capacity_mah_g=I*t[-1]*1000/s.p.nmc_mass_g,
                    theta_initial=1-soc[0],theta_final=1-soc[-1],
                    mass_balance_pct=100*np.max(abs(soc-(soc[0]-signed*t/inventory))),
                    current_balance_final_pct=100*abs(s.aL*(s.wx@j)-signed/m['area'])/abs(signed/m['area'])))
                solutions[label,stage]=d
                d.to_csv(dest/f'{label}_C{rate}_{stage}.csv',index=False)
        for stage in ('charge','discharge'):
            a,b=solutions['FEM',stage],solutions['FVM',stage]
            end=min(a.time_h.iloc[-1],b.time_h.iloc[-1]); t=np.linspace(0,end,2001)
            err=np.interp(t,b.time_h,b.voltage_v)-np.interp(t,a.time_h,a.voltage_v)
            pairs.append(dict(rate=rate,stage=stage,rmse_mv=1000*np.sqrt(np.mean(err**2)),
                duration_difference_pct=100*(b.time_h.iloc[-1]-a.time_h.iloc[-1])/a.time_h.iloc[-1]))
        pd.DataFrame(rows).to_csv(dest/'prediction_metrics.csv',index=False)
        pd.DataFrame(pairs).to_csv(dest/'pair_metrics.csv',index=False)
    (dest/'metadata.json').write_text(json.dumps(dict(model_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),rates=list(rates),nx=nx,nr=nr,max_step_s=max_step,fit=False,reference='C20 collaborator model',status='prediction_not_validation'),indent=2))
    return pd.DataFrame(rows),pd.DataFrame(pairs)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model');p.add_argument('--outdir',default='outputs/v07');p.add_argument('--nx',type=int,default=4);p.add_argument('--nr',type=int,default=10);p.add_argument('--max-step',type=float,default=120);p.add_argument('--rates',nargs='+',type=int,default=[20,10,5]);a=p.parse_args()
    if min(a.rates)<=0 or a.max_step<=0: p.error('positive rate and step required')
    x,y=run(a.model,a.outdir,a.nx,a.nr,a.max_step,a.rates);print(x.to_string(index=False));print(y.to_string(index=False))
