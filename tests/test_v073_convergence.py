"""Numerical-control and convergence gates without any private data."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import paper_reproduction as paper
import run_v073_convergence as conv


def model():
    u = PchipInterpolator([0., 1.], [2.7, 4.3])
    return paper.PaperFEM({'charge':u, 'discharge':u}, *conv.PARAMS)


def test_explicit_defaults_match_implicit():
    m = model()
    a, ca, da = m.stage('charge', 20)
    b, cb, db = m.stage('charge', 20, max_step=120, rtol=1e-7, atol=1e-9, output_step=30)
    pd.testing.assert_frame_equal(a,b)
    np.testing.assert_array_equal(ca,cb)
    assert da==db and da['termination']=='voltage'
    assert da['final_voltage_v']==pytest.approx(4.2,abs=1e-8)


@pytest.mark.parametrize('options', [{'max_step':0}, {'rtol':float('nan')}, {'atol':-1}, {'output_step':0}])
def test_invalid_solver_options(options):
    with pytest.raises(ValueError,match='finite and positive'):
        model().stage('charge',20,**options)


def test_wrong_state_shape():
    with pytest.raises(ValueError,match='shape mismatch'):
        model().stage('discharge',20,np.ones((9,21)))


def test_comparison_no_extrapolation_and_gate():
    a=pd.DataFrame(dict(time_h=[0.,1.],voltage_v=[3.,4.]))
    b=pd.DataFrame(dict(time_h=[0.,1.,2.],voltage_v=[3.,4.,5.]))
    d=dict(capacity_mah_g=8.25,cutoff_h=1.,termination='voltage',mass_error_mah_g=0.,state_min=.1,state_max=.9)
    result=conv.compare(d,dict(d,cutoff_h=2.),a,b)
    assert result['voltage_rmse_mv']==pytest.approx(0.)
    assert result['coverage_new_pct']==pytest.approx(50.)
    assert not result['passed']
    assert conv.compare(d,d,a,a)['passed']
    assert not conv.compare(d,dict(d,state_max=1.1),a,a)['passed']


def test_input_hash_guard(tmp_path):
    (tmp_path/'ocv_charge_digitized.csv').write_text('soc,v\n0,2.7\n1,4.2\n')
    with pytest.raises(ValueError,match='hash mismatch'):
        conv.load_ocv(tmp_path)
