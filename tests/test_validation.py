import pandas as pd
import pytest
from solid_pinn.validation import capacity_ah,capacity_error_percent,compare_voltage_curve,PAPER_TABLE3_PERCENT


def test_paper_reported_errors_transcribed():
    assert PAPER_TABLE3_PERCENT[10]["discharge"] == -3.1


def test_capacity_metric_and_errors():
    f=pd.DataFrame({"time_h":[0,1,2],"stage":["charge"]*3,"current_a":[-0.001]*3})
    assert capacity_ah(f,"charge")==pytest.approx(0.002)
    assert capacity_error_percent(1.01,1.0)==pytest.approx(1.0)


def test_curve_rmse_on_identical_data():
    df=pd.DataFrame({"time_h":[0,1,2],"stage":["charge"]*3,"voltage_v":[3,3.5,4]})
    comp=compare_voltage_curve(df,df)
    assert comp.rmse_v.iloc[0]==pytest.approx(0.0)
