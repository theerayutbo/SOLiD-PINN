import sys
from pathlib import Path
import json
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import audit_open_benchmarks as a


def test_csv_profile_distinguishes_sentinels(tmp_path):
    p=tmp_path/"a.csv"
    p.write_text("id,x,y\n1,NR,N/A\n2,,3\n3\n")
    d=a.csv_profile(p)
    assert (d["rows"],d["columns"],d["malformed_rows"])==(3,3,1)
    assert d["fields"][1]["not_reported"]==1
    assert d["fields"][1]["blank"]==1
    assert d["fields"][2]["not_applicable"]==1


def test_missing_and_wrong_checksum_are_blocked(tmp_path):
    reg=tmp_path/"registry.json"
    reg.write_text(json.dumps({"sources":[{"id":"test","files":[{"name":"a.csv","url":"https://example.invalid/a","md5":"wrong"}]}]}))
    assert a.run(tmp_path,["test"],registry=reg)["files"][0]["status"]=="blocked"
    p=tmp_path/"test"/"a.csv";p.write_text("x\n1\n")
    d=a.run(tmp_path,["test"],registry=reg)["files"][0]
    assert d["status"]=="blocked" and "MD5" in d["error"]


def test_local_file_inventory(tmp_path):
    reg=tmp_path/"registry.json"
    reg.write_text(json.dumps({"sources":[{"id":"test","files":[{"name":"a.csv","url":"https://example.invalid/a"}]}]}))
    p=tmp_path/"test";p.mkdir();(p/"a.csv").write_text("x\n1\n")
    row=a.run(tmp_path,["test"],registry=reg)["files"][0]
    assert row["status"]=="inventoried"
    assert row["profile"]["rows"]==1 and len(row["sha256"])==64


def test_cp1252_csv_preserves_degree_symbol(tmp_path):
    p=tmp_path/"a.csv"
    p.write_bytes("id,temp °C\n1,25\n".encode("cp1252"))
    d=a.csv_profile(p)
    assert d["encoding"].startswith("cp1252")
    assert d["fields"][1]["name"]=="temp °C"


def test_html_is_not_workbook_or_csv(tmp_path):
    import pytest
    p=tmp_path/"bad.xlsx"
    p.write_bytes(b"<!doctype html><html>error</html>")
    with pytest.raises(ValueError,match="not an XLSX"):
        a.validate_workbook(p)
    with pytest.raises(ValueError,match="HTML response"):
        a.csv_profile(p)


def test_valid_workbook_headers(tmp_path):
    from openpyxl import Workbook
    p=tmp_path/"ok.xlsx"
    b=Workbook();b.active.append(["Time (s)","Voltage (V)"]);b.active.append([0,3.0]);b.save(p)
    d=a.xlsx_profile(p)
    assert d["sheets"][0]["header_candidates"][0]["label"]=="Time (s)"
