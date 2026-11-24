from pathlib import Path
import runpy
import numpy as np
import pytest
from scipy.interpolate import PchipInterpolator

p=runpy.run_path(str(Path(__file__).resolve().parents[1]/'scripts'/'paper_reproduction.py'))

def test_inventory_bounds():
    assert p['inventory'](.131)==pytest.approx(133.880729824)
    assert p['inventory'](p['Q']*3600/(p['F']*p['C']*p['L']*p['A']))==pytest.approx(165.)

def test_fem_instantaneous_mass_and_current():
    u=PchipInterpolator([0,1],[2.7,4.2]);m=p['PaperFEM']({'charge':u,'discharge':u},.131,.131,6.59173895,nx=4,nr=10)
    c=np.full(m.shape,.5)
    for sign,stage in [(-1,'charge'),(1,'discharge')]:
        I=sign*p['Q']/20
        v,j=m.fields(c[:,-1],I,stage)
        assert m.aL*(m.wx@j)==pytest.approx(I/p['A'],abs=1e-10)
        d=c@m.radial.T+j[:,None]*m.flux
        assert (m.wx@d@m.wr)*p['inventory'](m.eps)==pytest.approx(I*1000/(3600*p['M']),abs=1e-10)

def test_comparison_no_extrapolation():
    import pandas as pd
    a=pd.DataFrame(dict(time_h=[0.,1.],voltage_v=[3.,4.]))
    b=pd.DataFrame(dict(time_h=[0.,1.,2.],voltage_v=[3.,4.,5.]))
    r=p['metrics'](a,b,20)
    assert r['rmse_mv']==pytest.approx(0.)
    assert r['coverage_pct']==pytest.approx(50.)
