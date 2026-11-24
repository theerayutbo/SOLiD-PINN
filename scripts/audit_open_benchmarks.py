"""Inventory published benchmark files, never normalize unknown units or fit models."""
import argparse
import csv
import hashlib
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
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
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
        return dict(rows=rows, columns=len(header), malformed_rows=malformed,
                    duplicate_header_count=len(header)-len(set(header)),
                    fields=[dict(index=i, name=name, **counts[i]) for i,name in enumerate(header)],
                    note="Literal sentinel classification only; verify against publisher manual.")


def xlsx_profile(path):
    from openpyxl import load_workbook
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        sheets = []
        for sheet in book.worksheets:
            # Dimensions are workbook metadata, not audited record counts.
            sample = list(sheet.iter_rows(min_row=1, max_row=12, max_col=min(sheet.max_column or 40, 40), values_only=True))
            sheets.append(dict(name=sheet.title, declared_rows=sheet.max_row,
                               declared_columns=sheet.max_column,
                               populated_sample_cells=sum(v is not None for row in sample for v in row),
                               sample_rows_examined=len(sample)))
        return dict(sheets=sheets, note="Inventory only; inspect units, headers, group identity and time/current availability before adapter design.")
    finally:
        book.close()


def acquire(item, path):
    tmp = path.with_suffix(path.suffix + ".part")
    try:
        with urllib.request.urlopen(item["url"], timeout=60) as src, tmp.open("wb") as dst:
            size = 0
            for block in iter(lambda: src.read(1024 * 1024), b""):
                size += len(block)
                if size > 250 * 1024 * 1024:
                    raise ValueError("download exceeds 250 MiB cap")
                dst.write(block)
        if item.get("md5") and hashes(tmp)["md5"] != item["md5"]:
            raise ValueError("publisher MD5 mismatch")
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
