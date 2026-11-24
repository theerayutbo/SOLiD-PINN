"""Inventory published benchmark files, never normalize unknown units or fit models."""
import argparse
import csv
import hashlib
import io
import zipfile
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "benchmarks" / "registry.json"


def hashes(path):
    sha = hashlib.sha256()
    md = hashlib.md5(usedforsecurity=False)
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
            md.update(block)
    return {"sha256": sha.hexdigest(), "md5": md.hexdigest()}


def csv_profile(path):
    raw = Path(path).read_bytes()
    try:
        decoded = raw.decode("utf-8-sig")
        encoding = "utf-8-sig"
    except UnicodeDecodeError:
        decoded = raw.decode("cp1252", errors="strict")
        encoding = "cp1252 (provisional; verify publisher encoding)"
    if decoded.lstrip().lower().startswith(("<!doctype html", "<html")):
        raise ValueError("HTML response, not CSV")
    with io.StringIO(decoded, newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader, [])
        if not header:
            raise ValueError("empty CSV")
        counts = [dict(blank=0, not_reported=0, not_applicable=0) for _ in header]
        rows = malformed = 0
        for row in reader:
            if not any(v.strip() for v in row):
                continue
            rows += 1
            if len(row) != len(header):
                malformed += 1
                continue
            for i, value in enumerate(row):
                v = value.strip().casefold()
                if not v:
                    counts[i]["blank"] += 1
                elif v in {"not reported", "nr", "n.r."}:
                    counts[i]["not_reported"] += 1
                elif v in {"not applicable", "n/a", "na"}:
                    counts[i]["not_applicable"] += 1
        return dict(rows=rows, columns=len(header), malformed_rows=malformed, encoding=encoding,
                    duplicate_header_count=len(header)-len(set(header)),
                    fields=[dict(index=i, name=name, **counts[i]) for i,name in enumerate(header)],
                    note="Literal sentinel classification only; verify against publisher manual.")


def xlsx_profile(path):
    from openpyxl import load_workbook
    validate_workbook(path)
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        sheets = []
        for sheet in book.worksheets:
            # Dimensions are workbook metadata, not audited record counts.
            sample = list(sheet.iter_rows(min_row=1, max_row=12, max_col=min(sheet.max_column or 100, 100), values_only=True))
            sheets.append(dict(name=sheet.title, declared_rows=sheet.max_row,
                               declared_columns=sheet.max_column,
                               populated_sample_cells=sum(v is not None for row in sample for v in row),
                               sample_rows_examined=len(sample),
                               header_candidates=[dict(row=i+1, column=j+1, label=v[:160])
                                                  for i,row in enumerate(sample[:6])
                                                  for j,v in enumerate(row) if isinstance(v,str) and v.strip()][:120]))
        return dict(sheets=sheets, note="Inventory only; inspect units, headers, group identity and time/current availability before adapter design.")
    finally:
        book.close()


def validate_workbook(path):
    if not zipfile.is_zipfile(path):
        raise ValueError("not an XLSX ZIP archive; possible publisher error page")
    with zipfile.ZipFile(path) as z:
        if not {"[Content_Types].xml", "xl/workbook.xml"} <= set(z.namelist()):
            raise ValueError("ZIP does not contain XLSX workbook metadata")


def quarantine_known_bad(path):
    # Only quarantine the exact invalid payload identified in the submitted inventory.
    if path.suffix == ".xlsx" and path.is_file() and hashes(path)["sha256"] == "32ed63159c77e21ee19ca1b9aa3213ccf0218eb59539560b132a8e68ef0e18ea":
        dest = path.with_name(path.name + ".invalid-32ed6315")
        if dest.exists():
            if hashes(dest)["sha256"] != hashes(path)["sha256"]:
                raise ValueError("quarantine collision")
            path.unlink()
        else:
            path.rename(dest)


def acquire(item, path):
    tmp = path.with_suffix(path.suffix + ".part")
    try:
        request = urllib.request.Request(item["url"], headers={"User-Agent":"SOLiD-PINN benchmark inventory/0.8.1", "Accept":"application/octet-stream, */*"})
        with urllib.request.urlopen(request, timeout=60) as src, tmp.open("wb") as dst:
            size = 0
            for block in iter(lambda: src.read(1024 * 1024), b""):
                size += len(block)
                if size > 250 * 1024 * 1024:
                    raise ValueError("download exceeds 250 MiB cap")
                dst.write(block)
        if item.get("md5") and hashes(tmp)["md5"] != item["md5"]:
            raise ValueError("publisher MD5 mismatch")
        if path.suffix == ".xlsx":
            validate_workbook(tmp)
        elif path.suffix == ".csv":
            csv_profile(tmp)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def run(cache, selected, download=False, registry=REGISTRY):
    sources = json.loads(Path(registry).read_text())["sources"]
    known = {s["id"] for s in sources}
    if not set(selected) <= known:
        raise ValueError("unknown source id")
    results = []
    for source in sources:
        if source["id"] not in selected:
            continue
        for item in source["files"]:
            path = Path(cache)/source["id"]/item["name"]
            path.parent.mkdir(parents=True, exist_ok=True)
            row = dict(source=source["id"], file=item["name"], url=item["url"])
            try:
                if download:
                    quarantine_known_bad(path)
                if not path.exists() and download:
                    acquire(item, path)
                if not path.is_file():
                    raise FileNotFoundError("file not available")
                digests = hashes(path)
                if item.get("md5") and digests["md5"] != item["md5"]:
                    raise ValueError("publisher MD5 mismatch")
                row.update(bytes=path.stat().st_size, **digests)
                row["profile"] = csv_profile(path) if path.suffix == ".csv" else xlsx_profile(path)
                row["status"] = "inventoried"
            except Exception as exc:
                row.update(status="blocked", error=f"{type(exc).__name__}: {exc}")
            results.append(row)
    return dict(schema=1, scope="file inventory only; not model-ready validation", files=results)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--source", action="append", choices=["umd", "puls2024", "liopa"])
    p.add_argument("--download", action="store_true")
    a = p.parse_args()
    result = run(a.cache, a.source or ["umd", "puls2024"], a.download)
    dest = Path(a.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({s:sum(r["status"]==s for r in result["files"]) for s in ("inventoried","blocked")}))
    raise SystemExit(1 if any(r["status"]!="inventoried" for r in result["files"]) else 0)
