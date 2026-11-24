import numpy as np
import pytest
from test_comsol_transfer import synthetic_model
from solid_pinn.transfer_fvm import TransferFVM

@pytest.mark.parametrize('stage,sign',[('charge',-1),('discharge',1)])
def test_conservation(stage,sign):
    m=synthetic_model();s=TransferFVM(m,4,6)
    c=np.tile(np.linspace(.65,.7,len(s.r)),(len(s.x),1))
    I=sign*s.p.current_a(20); f=s.fields(c[:,-1],I,stage)
    assert s.aL*(s.wx@f.reaction)==pytest.approx(I/m['area'],abs=1e-10)
    expected=I/(m['area']*m['L']*m['eps']*m['F']*m['cmax'])
    assert s.wx@s.rhs(c,I,stage)@s.wr==pytest.approx(expected,rel=1e-10)
