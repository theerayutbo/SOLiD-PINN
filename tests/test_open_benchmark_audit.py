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
