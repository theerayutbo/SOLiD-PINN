import numpy as np
import pytest
from solid_pinn.comsol_c20 import load_c20_cycle, compare_cycle

def test_switch_preserves_both_sides(tmp_path):
    path=tmp_path/"trace.txt"
    path.write_text("% Model: example.mph\n% Time (h) Cell potential\n0 2.73\n1 3.7\n2 4.2\n2.000000000000001 4.15\n3 3.8\n4 2.714\n")
    df,meta=load_c20_cycle(path)
    assert len(df)==6
    assert meta["switch_drop_mv"]==pytest.approx(50)
    assert not meta["last_sample_is_2p7v"]
    assert list(df[df.stage=="discharge"].time_h)==pytest.approx([0,1,2])
    model={stage:df[df.stage==stage].assign(cell_soc=.5) for stage in ("charge","discharge")}
    assert all(r["rmse_mv"]<1e-9 for r in compare_cycle(df,model))

def test_missing_event_rejected(tmp_path):
    p=tmp_path/"bad.txt"
    np.savetxt(p,[[0,2.7],[1,3.6],[2,4.2],[3,4.1],[4,3.8],[5,2.7]])
    with pytest.raises(ValueError,match="paired-time"): load_c20_cycle(p)
