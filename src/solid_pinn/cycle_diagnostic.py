"""Conditional rate/fade diagnostics; does not identify causal mechanisms."""
from pathlib import Path
import argparse
import hashlib
import numpy as np
import pandas as pd

BLOCKS = [(1,3,30),(4,8,20),(9,13,10),(14,18,5),(19,20,2),(21,50,20)]
TABLE_CYCLES = [3,8,13,18,20,25,30,35,40,45,50]
TABLE_RETENTION = {'charge':[97.45,87.35,75.13,60.68,34.59,81.06,77.33,75.84,71.76,68.91,65.67], 'discharge':[97.92,86.44,74.11,59.12,33.20,79.84,77.18,72.85,71.28,69.10,68.30]}


def read_cycle(path, stage):
    if stage not in TABLE_RETENTION:
        raise ValueError('invalid stage')
    df = pd.read_csv(path)
    c = df['Cycle'].to_numpy(float)
    q = df['Capacity [mAh/g]'].to_numpy(float)
    ret = df[f'{stage.capitalize()} retention [%]'].to_numpy(float)
    if not np.array_equal(c, np.arange(1,51)) or not np.isfinite(np.c_[q,ret]).all() or np.any(q<=0):
        raise ValueError('expected 50 ordered positive finite capacity observations')
    if not np.allclose(ret,100*q/q[1],rtol=0,atol=.012):
        raise ValueError('retention is inconsistent with cycle 2')
    if not np.allclose(ret[np.array(TABLE_CYCLES)-1],TABLE_RETENTION[stage],rtol=0,atol=.005):
        raise ValueError('Table 1 retention anchors do not match; do not assume protocol')
    return q


def summarize(q, stage):
    q=np.asarray(q,float)
    if q.shape!=(50,) or not np.isfinite(q).all() or np.any(q<=0):
        raise ValueError('invalid cycle data')
    blocks=[]; recovery=[]; bounds=[]; fits=[]
    for a,b,r in BLOCKS:
        y=q[a-1:b]
        blocks.append(dict(stage=stage,start_cycle=a,end_cycle=b,rate_denominator=r,mean_capacity_mah_g=y.mean(),first_capacity_mah_g=y[0],last_capacity_mah_g=y[-1]))
    gap=q[7]-q[19]
    if gap<=0:
        raise ValueError('expected positive pre-return capacity gap')
    for n in (21,22):
        recovery.append(dict(stage=stage,return_cycle=n,capacity_gain_from_cycle20_mah_g=q[n-1]-q[19],recovered_fraction_of_cycle8_to20_drop_pct=100*(q[n-1]-q[19])/gap,same_rate_gap_vs_cycle8_mah_g=q[7]-q[n-1],subsequent_fade_to50_mah_g=q[n-1]-q[49],subsequent_fade_to50_pct=100*(q[n-1]-q[49])/q[n-1]))
    # Retrospective only: assume unobserved C20 baseline stays between cycles 8/22.
    for a,b,r in BLOCKS[2:5]:
        obs=q[a-1:b].mean()
        interp=(q[7]+(q[21]-q[7])*(np.arange(a,b+1)-8)/14).mean()
        bounds.append(dict(stage=stage,rate_denominator=r,observed_mean_mah_g=obs,conditional_loss_low_mah_g=min(q[7],q[21])-obs,conditional_loss_high_mah_g=max(q[7],q[21])-obs,interpolated_loss_mah_g=interp-obs))
    # Fixed chronological split; cycle 21 inclusion is a sensitivity analysis.
    for start in (21,22):
        x=np.arange(start,51)-start; y=q[start-1:]; train=x<=35-start; test=~train
        slope,intercept=np.polyfit(x[train],y[train],1)
        exp_slope,exp_intercept=np.polyfit(x[train],np.log(y[train]),1)
        for model,pred in [('constant',np.full(len(y),y[train].mean())),('linear',intercept+slope*x),('exponential',np.exp(exp_intercept+exp_slope*x))]:
            fits.append(dict(stage=stage,train_start=start,train_end=35,test_start=36,test_end=50,model=model,train_rmse_mah_g=np.sqrt(np.mean((pred[train]-y[train])**2)),test_rmse_mah_g=np.sqrt(np.mean((pred[test]-y[test])**2)),test_bias_mah_g=np.mean(pred[test]-y[test]),pred_cycle50_mah_g=pred[-1],actual_cycle50_mah_g=y[-1],linear_slope_mah_g_per_cycle=slope if model=='linear' else np.nan))
    return blocks,recovery,bounds,fits


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input_dir');p.add_argument('--outdir',default='outputs/v071');a=p.parse_args()
    root=Path(a.input_dir);dest=Path(a.outdir);dest.mkdir(parents=True,exist_ok=True)
    allrows=[[],[],[],[]]
    for stage in ('charge','discharge'):
        path=root/f'{stage.capitalize()}_50cycle_new.csv';q=read_cycle(path,stage)
        print(path.name,hashlib.sha256(path.read_bytes()).hexdigest())
        for rows,more in zip(allrows,summarize(q,stage)): rows.extend(more)
    for name,rows in zip(('blocks','recovery','conditional_loss','fade_backtest'),allrows):
        df=pd.DataFrame(rows);df.to_csv(dest/f'{name}.csv',index=False);print(name);print(df.to_string(index=False))

if __name__=='__main__': main()
