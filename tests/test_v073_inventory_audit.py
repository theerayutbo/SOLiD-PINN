import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import pytest
from run_v073_inventory_audit import ACTIVE_FRACTION, DENSITY, FULL_CAPACITY, WINDOW, LOADING_KG_M2, mapped_ocv
from paper_reproduction import inventory,L

def test_mass_closure():
    assert DENSITY*L*ACTIVE_FRACTION == pytest.approx(LOADING_KG_M2)
    assert inventory(ACTIVE_FRACTION) == pytest.approx(FULL_CAPACITY)
    assert FULL_CAPACITY*WINDOW == pytest.approx(165)

def test_ocv_map():
    f=mapped_ocv({'charge':lambda x:x,'discharge':lambda x:2*x},WINDOW)
    np.testing.assert_allclose(f['charge'](np.array([0,WINDOW/2,WINDOW,1])),[0,.5,1,1])
    assert f['discharge'](WINDOW/2)==pytest.approx(1)
    with pytest.raises(ValueError): mapped_ocv({},0)
