"""Integrity tests for the published *historical* calibration ledger.

No experimental-curve data or copyrighted figure arrays are redistributed.
These tests check arithmetic/provenance consistency only; they do not
independently reproduce previous calibration runs.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "calibration_trial_metrics.csv"
REPORT = ROOT / "docs" / "calibration_experiment_ledger.md"


def _read_trials():
    with LEDGER.open(newline="", encoding="utf-8") as fh:
        return {row["trial_id"]: row for row in csv.DictReader(fh)}


def test_all_documented_variants_are_registered():
    trials = _read_trials()
    assert len(trials) == 10
    assert {"baseline", "imothep_25pct", "imothep_50pct",
            "imothep_ds", "asr_0", "asr_0p8", "asr_5",
            "asr_50", "asr_200", "asr_500"} <= trials.keys()


def test_heldout_mean_is_not_training_only():
    trials = _read_trials()
    for key in ("baseline", "imothep_25pct", "imothep_50pct", "imothep_ds"):
        row = trials[key]
        rmse = [
            float(row[f"c{rate}_{stage}_rmse_mv"])
            for rate in (10, 5) for stage in ("charge", "discharge")
        ]
        calculated = sum(rmse) / 4
        assert abs(calculated - float(row["heldout_mean_rmse_mv"])) < 0.015


def test_negative_results_are_preserved_as_not_adopted():
    trials = _read_trials()
    assert float(trials["imothep_25pct"]["heldout_mean_rmse_mv"]) > float(
        trials["baseline"]["heldout_mean_rmse_mv"]
    )
    assert trials["imothep_25pct"]["disposition"] == "rejected"
    assert trials["imothep_50pct"]["disposition"] == "rejected"
    assert trials["imothep_ds"]["disposition"] == "inconclusive_not_adopted"
    assert trials["asr_0"]["disposition"] == "selected_grid_baseline"
    for key in ("asr_0p8", "asr_5", "asr_50", "asr_200", "asr_500"):
        assert trials[key]["disposition"] == "not_selected"
        assert trials[key]["heldout_mean_rmse_mv"] == ""


def test_source_references_and_rights_warnings_are_present():
    text = REPORT.read_text(encoding="utf-8")
    for cite in ("10.1016/j.ceja.2024.100610", "10.1002/advs.202302521",
                 "10.1038/s41560-024-01634-3", "10.5281/zenodo.15688067",
                 "10.1038/s41467-022-34855-9", "10.5334/jors.309",
                 "imothep-project.eu"):
        assert cite in text
    assert "not committed publicly" in text
    assert "not ingested" in text.lower()
