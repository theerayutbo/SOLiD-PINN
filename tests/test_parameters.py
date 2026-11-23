import pytest
from solid_pinn.parameters import Parameters
from solid_pinn.ocv import ocv_v


def test_paper_geometry_and_nominal_current():
    p=Parameters()
    assert p.area_m2==pytest.approx(2.83e-5)
    assert p.separator_m==pytest.approx(725e-6)
    assert p.nominal_capacity_ah==pytest.approx(0.000233475)
    assert p.current_a(20)==pytest.approx(0.000233475/20)


def test_paper_table_two_is_not_perfectly_complete():
    p=Parameters()
    assert 0.1 < p.active_volume_fraction_inferred < 0.2
    assert 0.0 < p.kappa_cathode_effective < p.kappa_sse_s_m


def test_ocv_charge_discharge_difference_at_half_soc():
    assert float(ocv_v(0.5,"charge") - ocv_v(0.5,"discharge"))==pytest.approx(0.033)


def test_experimental_ocv_loader(tmp_path):
    import pandas as pd
    from solid_pinn.ocv import experimental_ocv_from_csv
    files=[]
    for stage, bump in (("charge",0.02),("discharge",-0.02)):
        f=tmp_path/f"{stage}.csv"
        pd.DataFrame({"soc":[0,0.5,1],"voltage_v":[3,3.7,4.2]}).assign(
            voltage_v=lambda df: df.voltage_v+bump).to_csv(f,index=False)
        files.append(str(f))
    u=experimental_ocv_from_csv(*files)
    assert float(u(0.5,"charge") - u(0.5,"discharge"))==pytest.approx(0.04)
