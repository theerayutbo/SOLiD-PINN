import numpy as np
import pandas as pd
import pytest
from solid_pinn.cycle_diagnostic import read_cycle, summarize, TABLE_CYCLES, TABLE_RETENTION


def test_synthetic_recovery_and_frozen_linear():
    q=np.full(50,140.);q[19]=50.;q[20]=95.;q[21:]=130.-.5*np.arange(29)
    blocks,recovery,bounds,fits=summarize(q,'charge')
    assert len(blocks)==6 and len(bounds)==3 and len(fits)==6
    assert recovery[1]['recovered_fraction_of_cycle8_to20_drop_pct']==pytest.approx(100*80/90)
    row=next(r for r in fits if r['train_start']==22 and r['model']=='linear')
    assert row['test_rmse_mah_g']<1e-10
    altered=q.copy();altered[35:]-=10
    row2=next(r for r in summarize(altered,'charge')[3] if r['train_start']==22 and r['model']=='linear')
    assert row2['pred_cycle50_mah_g']==pytest.approx(row['pred_cycle50_mah_g'])
    assert row2['test_rmse_mah_g']==pytest.approx(10.)


def test_table_anchor_and_order_validation(tmp_path):
    ret=np.full(50,90.);ret[1]=100.;ret[np.array(TABLE_CYCLES)-1]=TABLE_RETENTION['charge']
    df=pd.DataFrame({'Cycle':np.arange(1,51),'Capacity [mAh/g]':ret*1.6,'Charge retention [%]':ret})
    p=tmp_path/'data.csv';df.to_csv(p,index=False)
    assert len(read_cycle(p,'charge'))==50
    df.loc[7,'Charge retention [%]']+=1;df.loc[7,'Capacity [mAh/g]']+=1.6;df.to_csv(p,index=False)
    with pytest.raises(ValueError,match='Table 1'):read_cycle(p,'charge')
    df.loc[0,'Cycle']=2;df.to_csv(p,index=False)
    with pytest.raises(ValueError,match='ordered'):read_cycle(p,'charge')


def test_invalid_data():
    with pytest.raises(ValueError):summarize(np.ones(49),'charge')
    with pytest.raises(ValueError):summarize(np.zeros(50),'charge')
