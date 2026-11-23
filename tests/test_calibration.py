import numpy as np
import pandas as pd
import pytest

from solid_pinn.calibration import (
    calibrate_c20, load_trace_csv, trace_diagnostics, validate_heldout,
)
from solid_pinn.numerical import ReducedP2D
from solid_pinn.ocv import ocv_v
from solid_pinn.parameters import Parameters


def test_trace_loader_requires_both_stages_and_increasing_time(tmp_path):
    f=tmp_path/"trace.csv"
    pd.DataFrame({"time_h":[0,1,2],"voltage_v":[3,3.2,3.4],
                  "stage":["charge"]*3}).to_csv(f,index=False)
    with pytest.raises(ValueError,match="both charge and discharge"):
        load_trace_csv(f)
    pd.DataFrame({"time_h":[0,1,2,3,4,4],"voltage_v":[3,3.2,3.4,4,3.8,3.7],
                  "stage":["charge"]*3+["discharge"]*3}).to_csv(f,index=False)
    with pytest.raises(ValueError,match="strictly increasing"):
        load_trace_csv(f)


def test_trace_diagnostics_identical_curves():
    x=pd.DataFrame({"time_h":[0,1,2,2,3,4],"voltage_v":[3,3.4,4.2,4.1,3.6,2.7],
                    "stage":["charge"]*3+["discharge"]*3})
    report=trace_diagnostics(x,x)
    for stage in ("charge","discharge"):
        assert report[stage]["rmse_v"]==pytest.approx(0)
        assert report[stage]["duration_error_h"]==pytest.approx(0)


def test_training_uses_only_c20_and_rejects_heldout_leakage():
    model=ReducedP2D(nx=2,nr=3)
    data=model.simulate_cycle(20,dt_s=1200)
    calibrated=calibrate_c20(data,ocv_v,nx=2,nr=3,dt_s=1200,
                             max_nfev=3,fit_initial_soc=False)
    assert calibrated.fit_report["training_rate"]=="C/20"
    assert calibrated.fit_report["objective_evaluations"]>0
    with pytest.raises(ValueError,match="held-out"):
        validate_heldout(calibrated,ocv_v,{20:data})
