"""Check immutable baseline inputs and archived synthetic evidence (no fitting)."""
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def blob(path):
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def verify(root=ROOT):
    root = Path(root)
    m = json.loads((root / "docs/research_baseline_v090b.json").read_text())
    for exp in m["experiments"]:
        for key in ("source", "test"):
            require(blob(root / exp[key]) == exp[key + "_blob"], f"changed {exp[key]}")
        require((root / exp["report"]).is_file(), f"missing {exp['report']}")
    for path, digest in m["additional_blobs"].items():
        require(blob(root / path) == digest, f"changed {path}")
    for path, digest in m["archives"].items():
        require(hashlib.sha256((root / path).read_bytes()).hexdigest() == digest,
                f"changed archive {path}")
    d = json.loads((root / "docs/results/colab/v090b_summary.json").read_text())
    expected = set(itertools.product(("null", "rest", "peak"), (1, 5), (11, 23, 37),
                                     ((8, 12), (32, 48), (128, 192)),
                                     ("calibrated", "linear", "rbf", "oracle")))
    keys = [(r["truth"], r["noise"], r["seed"], tuple(r["mesh"]), r["method"]) for r in d["metrics"]]
    require(len(keys) == len(expected) and set(keys) == expected, "incomplete/duplicate fit keys")
    for row in d["metrics"]:
        require(row["success"] is True, "failed fit")
        for key in ("test_rmse_mv", "extra_rmse_mv", "train_rmse_mv", "closure_rmse"):
            require(math.isfinite(row[key]) and row[key] >= 0, f"invalid metric {key}")
        require(all(math.isfinite(v) for v in row["params"]), "nonfinite fit parameter")
    pairs = ("(32, 48)->(64, 96)", "(64, 96)->(128, 192)")
    require(set(d["mesh"]) == {"train", "test", "extra"}, "missing mesh profiles")
    final = [v["delta_mv"][pair] for v in d["mesh"].values() for pair in pairs]
    require(d["mesh_gate_passed"] is True and all(math.isfinite(v) and 0 <= v <= 1 for v in final),
            "mesh gate failed")
    print(f"Archive verification: {len(keys)} unique fits; final mesh max {max(final):.6f} mV")
    print("All declared source/test blobs and archive SHA-256 digests match.")
    return {"fits": len(keys), "max_final_mesh_delta_mv": max(final)}

if __name__ == "__main__":
    verify()
