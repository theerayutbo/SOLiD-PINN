import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pytest
import run_v073_reference_audit as a


def test_switch_interval(tmp_path,monkeypatch):
    p=tmp_path/'trace.csv'
    p.write_text('t,v\n0,2.7\n2,4.19\n2.1,4.1\n4.5,2.7\n')
    monkeypatch.setitem(a.REF_HASHES,20,a.sha(p))
    d=a.audit(p,20)
    assert d['excess_min_mah_g']==pytest.approx(2.475)
    assert d['excess_max_mah_g']==pytest.approx(4.125)
    assert d['initial_theta_upper_bound_at_mass_inventory']<1


def test_hash_guard(tmp_path):
    p=tmp_path/'trace.csv';p.write_text('t,v\n0,2.7\n1,4.2\n2,2.7\n')
    with pytest.raises(ValueError,match='hash mismatch'):a.audit(p,20)


def test_duplicate_and_backward_timestamps(tmp_path,monkeypatch):
    p=tmp_path/'trace.csv';p.write_text('t,v\n0,2.7\n1,4.19\n1,4.1\n2,2.7\n')
    monkeypatch.setitem(a.REF_HASHES,20,a.sha(p))
    assert a.audit(p,20)['duplicate_timestamps']==1
    p.write_text('t,v\n0,2.7\n1,4.19\n0.9,4.1\n2,2.7\n')
    monkeypatch.setitem(a.REF_HASHES,20,a.sha(p))
    with pytest.raises(ValueError,match='invalid reference'):a.audit(p,20)
