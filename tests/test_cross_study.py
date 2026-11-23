import numpy as np
import pytest
from solid_pinn.cross_study import blended_ocv, imothep_nmc622_ocv


def test_imothep_formula_has_correct_stoichiometry_direction():
    assert float(imothep_nmc622_ocv(0.0, "charge")) == pytest.approx(3.02452, abs=2e-5)
    assert float(imothep_nmc622_ocv(1.0, "discharge")) == pytest.approx(4.11707, abs=2e-5)
    assert float(imothep_nmc622_ocv(0.5, "charge")) == pytest.approx(
        float(imothep_nmc622_ocv(0.5, "discharge")), abs=1e-13)


def test_external_weight_is_predeclared_and_bounded():
    def paper(soc, stage):
        return np.asarray(soc) * 0 + (3.3 if stage == "charge" else 3.1)
    assert float(blended_ocv(paper, 0.0)(0.3, "charge")) == pytest.approx(3.3)
    assert float(blended_ocv(paper, 1.0)(0.3, "charge")) == pytest.approx(
        float(imothep_nmc622_ocv(0.3, "charge")))
    assert float(blended_ocv(paper, 0.25)(0.3, "charge")) == pytest.approx(
        0.75 * 3.3 + 0.25 * float(imothep_nmc622_ocv(0.3, "charge")))
    with pytest.raises(ValueError):
        blended_ocv(paper, 1.1)
    with pytest.raises(ValueError):
        imothep_nmc622_ocv(float("nan"), "charge")
