"""Synthetic tests for checkpoint recovery; no private data or network required."""
import importlib
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
r=importlib.import_module("run_paper_resumable")

def test_roundtrip_and_reject_wrong_identity(tmp_path):
    p=tmp_path/"stage.npz"
    row=dict(case="literal_0131",rate=20,stage="charge",termination="voltage")
    c=np.full((5,11),.5)
    pred=pd.DataFrame(dict(time_h=[0.,1.],voltage_v=[2.8,4.2]))
    r.save_stage(p,row,c,pred)
    loaded,state,trace=r.load_stage(p,c.shape,"literal_0131",20,"charge")
    assert loaded==row
    np.testing.assert_array_equal(state,c)
    pd.testing.assert_frame_equal(trace,pred)
    with pytest.raises(ValueError,match="identity"):
        r.load_stage(p,c.shape,"literal_0131",20,"discharge")
    with pytest.raises(ValueError,match="invalid checkpoint"):
        r.load_stage(p,(3,3),"literal_0131",20,"charge")

def test_resume_propagates_charge_state_and_rebuilds_csv(tmp_path,monkeypatch):
    run=tmp_path/"run";run.mkdir()
    monkeypatch.setattr(r,"setup",lambda *a:(run,{}))
    monkeypatch.setattr(r.paper,"split_ref",lambda *a:{s:pd.DataFrame(dict(time_h=[0.,1.],voltage_v=[3.,4.])) for s in r.STAGES})
    calls=[]
    class Fake:
        shape=(5,11)
        def __init__(self,*a):pass
        def stage(self,s,rate,c):
            calls.append(s)
            if s=="discharge":np.testing.assert_array_equal(c,np.full(self.shape,.5))
            else:assert c is None
            trace=pd.DataFrame(dict(time_h=[0.,1.],voltage_v=[3.,4.]))
            return trace,np.full(self.shape,.5),dict(capacity_mah_g=8.25,termination="voltage",final_voltage_v=4.,mass_error_mah_g=0.)
    monkeypatch.setattr(r.paper,"PaperFEM",Fake)
    r.run_cases(tmp_path,tmp_path,["literal_0131"],[20],limit=1)
    assert calls==["charge"]
    (run/"literal_0131_20_charge.csv").unlink()
    r.run_cases(tmp_path,tmp_path,["literal_0131"],[20])
    assert calls==["charge","discharge"]
    assert (run/"literal_0131_20_charge.csv").exists()
    assert len(pd.read_csv(run/"metrics.csv"))==2

def test_manifest_changes_when_inputs_change(tmp_path,monkeypatch):
    base=tmp_path/"input";base.mkdir()
    (base/"SOLiD-PINN-OCV-Figure4").mkdir()
    for s in r.STAGES:
        (base/"SOLiD-PINN-OCV-Figure4"/f"ocv_{s}_digitized.csv").write_text("soc,v\n0,2.7\n1,4.2\n")
    for rate in r.RATES:
        (base/f"Ref_data_at_C{rate}.csv").write_text("t,v\n0,2.7\n1,4.2\n2,2.7\n")
    monkeypatch.setattr(r,"commit",lambda:"test-revision")
    out=tmp_path/"outputs"
    first,_=r.setup(base,out)
    second,_=r.setup(base,out)
    assert first==second
    (base/"Ref_data_at_C20.csv").write_text("t,v\n0,2.8\n1,4.2\n2,2.7\n")
    third,_=r.setup(base,out)
    assert first!=third


def test_execution_status_distinguishes_partial_failure_and_complete():
    cases, rates = ["literal_0131"], [20]
    charge = dict(case=cases[0], rate=20, stage="charge", status="complete")
    discharge = dict(case=cases[0], rate=20, stage="discharge", status="complete")
    other = dict(case="inventory_derived", rate=5, stage="charge", status="failure")
    failure = dict(discharge, status="failure")
    assert r.execution_status([charge, other], cases, rates, 1)["status"] == "partial"
    assert r.execution_status([charge], cases, rates)["status"] == "failed"
    assert r.execution_status([charge, failure], cases, rates, 1)["status"] == "failed"
    result = r.execution_status([charge, discharge, other], cases, rates)
    assert result == dict(status="complete", completed=2, expected=2, failed=[], missing=[])


@pytest.mark.parametrize("limit,stage_status,expected", [
    (1, "complete", 0), (None, "complete", 1), (1, "failure", 1),
])
def test_cli_exit_status(tmp_path, monkeypatch, limit, stage_status, expected):
    argv = ["runner", str(tmp_path), "--outdir", str(tmp_path),
            "--case", "literal_0131", "--rate", "20"]
    if limit is not None:
        argv += ["--limit-new-stages", str(limit)]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(r, "run_cases", lambda *args: tmp_path)
    monkeypatch.setattr(r, "summary", lambda run: [
        dict(case="literal_0131", rate=20, stage="charge", status=stage_status)])
    assert r.main() == expected
