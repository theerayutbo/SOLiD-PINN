import numpy as np
import pytest
from solid_pinn.comsol_multirate import load_wide_cycle


def write_trace(tmp_path, mismatch=False):
    p=tmp_path/"wide.txt"
    rows=np.array([[0,2.7,1e-5],[1,3.8,1e-5],[2,4.2,1e-5],
                   [2,4.1,-1e-5],[3,3.6,-1e-5],[4,2.71,-1e-5]])
    values=np.vstack([np.r_[0,rows.ravel()],np.r_[1,rows.ravel()]])
    if mismatch: values[1,2]+=.01
    with p.open("w") as f:
        f.write("% model\n"*7+"% X t (h) phis0 (V) Icell (A)\n")
        np.savetxt(f,values)
    return p


def test_wide_event_and_current_sign(tmp_path):
    df,meta=load_wide_cycle(write_trace(tmp_path),10,1e-5)
    assert len(df)==6 and meta["spatial_rows"]==2
    assert meta["switch_drop_mv"]==pytest.approx(100)
    assert not meta["last_sample_is_2p7v"]
    assert list(df.time_h)==[0,1,2,0,1,2]
    assert df.current_a.iloc[0]<0 and df.current_a.iloc[-1]>0


def test_non_global_export_and_wrong_current_rejected(tmp_path):
    with pytest.raises(ValueError,match="global values"):
        load_wide_cycle(write_trace(tmp_path,True),10,1e-5)
    with pytest.raises(ValueError,match="current magnitude"):
        load_wide_cycle(write_trace(tmp_path),10,2e-5)
