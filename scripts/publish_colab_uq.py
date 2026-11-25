"""Validate and publish synthetic v0.8.4 summary only; never upload arbitrary files."""
import base64
import hashlib
import json
import math
import re
from pathlib import Path
from urllib.parse import quote

REPO = "theerayutbo/SOLiD-PINN"
DESIGNS = ("single", "matched", "multi")
TRUTH = [25., 12., 15., .8]
SOURCE_BLOB = "71de1e9009ecbb192c3c65055aa83d1659d0c48d"
TEST_BLOB = "8c0cc248d0fe93451f7d0b24d476defdbd25130f"

def canonical(obj):
    return (json.dumps(obj, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def git_blob(raw):
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

def intervals(q, n):
    if len(q)!=3 or any(len(row)!=n for row in q):
        raise ValueError("invalid quantile dimensions")
    if any(not math.isfinite(x) for row in q for x in row):
        raise ValueError("nonfinite quantile")
    if any(not q[0][i]<=q[1][i]<=q[2][i] for i in range(n)):
        raise ValueError("unordered quantile")
    return q

def index_exact(rows, keys, expected):
    indexed={tuple(row[k] for k in keys):row for row in rows}
    if len(indexed)!=len(rows) or set(indexed)!=expected:
        raise ValueError(f"incomplete or duplicate {keys}")
    return indexed

def build_bundle(raw, revision, solver_bytes, test_bytes):
    if not re.fullmatch(r"[0-9a-f]{40}",revision):
        raise ValueError("invalid revision")
    if git_blob(solver_bytes)!=SOURCE_BLOB or git_blob(test_bytes)!=TEST_BLOB:
        raise ValueError("solver/test source differs from reviewed v0.8.4")
    d=json.loads(raw)
    if d["truth"]!=TRUTH or d["parameters"]!=["R0","Rinf","tau","j0"] or (d["n"],d["draws"],d["repeats"],d["coverage_noise_mv"],d["representative_seed"])!=(151,16000,30,5,11):
        raise ValueError("unexpected benchmark protocol")
    rep=index_exact(d["representative"],("design","noise","prior"),{(a,n,p) for a in DESIGNS for n in (1,5) for p in ("uniform","log_j0")})
    checks=index_exact(d["grid_checks"],("design","noise"),{(a,n) for a in DESIGNS for n in (1,5)})
    cov=index_exact(d["coverage"],("design","seed"),{(a,s) for a in DESIGNS for s in range(100,130)})
    summary=[]; refinement=[]; coverage=[]
    for (a,n,p),row in sorted(rep.items()):
        q=intervals(row["quantiles"],4); v=intervals(row["pred_quantiles"],2)
        acc=float(row["acceptance"])
        if not 0<acc<=1: raise ValueError("invalid rejection acceptance")
        summary.append(dict(design=a,noise_mv=n,prior=p,parameter_quantiles=q,latent_voltage_quantiles_mv=v,acceptance=acc))
    for (a,n),row in sorted(checks.items()):
        coarse=intervals(row["coarse"],4);fine=intervals(row["fine"],4)
        ratios=[abs(coarse[i][k]-fine[i][k])/max(1e-12,fine[2][k]-fine[0][k]) for i in range(3) for k in range(4)]
        refinement.append(dict(design=a,noise_mv=n,max_quantile_delta_over_fine_width=max(ratios),fine_parameter_quantiles=fine))
    for a in DESIGNS:
        counts=[0]*4; pred=[0]*2
        # Ground-truth latent voltage is calculated independently, not from reported booleans.
        t=40.; K=4*8.314*298.15/96485*1000
        r=TRUTH[1]+(TRUTH[0]-TRUTH[1])*math.exp(-t/TRUTH[2])
        vtruth=[2*j*r+K*math.asinh(j/(2*TRUTH[3])) for j in (1.,3.)]
        for seed in range(100,130):
            row=cov[(a,seed)];q=intervals(row["quantiles"],4);v=intervals(row["pred_quantiles"],2)
            for k in range(4): counts[k]+=int(q[0][k]<=TRUTH[k]<=q[2][k])
            for k in range(2): pred[k]+=int(v[0][k]<=vtruth[k]<=v[2][k])
        coverage.append(dict(design=a,repeats=30,noise_mv=5,parameter_covered=counts,latent_voltage_covered=pred))
    env={k:str(d["environment"][k]) for k in ("python","numpy","scipy")}
    # This explicit whitelist deliberately excludes individual fits, posterior samples, source data and credentials.
    return dict(schema=1,scope="synthetic analytical Bayesian reference only; not Bayesian PINN or experimental validation",source_revision=revision,solver_sha256=digest(solver_bytes),test_sha256=digest(test_bytes),full_private_report_sha256=digest(raw),environment=env,protocol=dict(truth=TRUTH,parameters=d["parameters"],grid_base=151,draws=16000,repeats=30,representative_seed=11,latent_prediction_time_h=40,latent_prediction_current_mA_cm2=[1,3]),completed=dict(representative=12,refinement=6,coverage=90,total=108),representative=summary,grid_refinement=refinement,coverage=coverage)

def publish(bundle, token, session=None):
    """Create immutable, content-addressed results branch; no token in URLs or logs."""
    import requests
    if not token or not token.strip(): raise ValueError("missing GitHub token")
    raw=canonical(bundle)
    revision=bundle["source_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}",revision): raise ValueError("invalid revision")
    tag=digest(raw)[:20]
    branch=f"results/v084-colab-{tag}"
    path="docs/results/colab/v084_summary.json"
    api=f"https://api.github.com/repos/{REPO}"
    s=session or requests.Session()
    headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
    def call(method, endpoint, **kwargs):
        return s.request(method,api+endpoint,headers=headers,timeout=45,**kwargs)
    def require(resp, allowed):
        if resp.status_code not in allowed:
            raise RuntimeError(f"GitHub API HTTP {resp.status_code}; inspect repository token permissions or retry")
        return resp
    refpath="/git/ref/heads/"+quote(branch,safe="/")
    ref=call("GET",refpath)
    if ref.status_code==404:
        require(call("POST","/git/refs",json={"ref":"refs/heads/"+branch,"sha":revision}),{201,422})
        ref=call("GET",refpath)
    head=require(ref,{200}).json()["object"]["sha"]
    endpoint="/contents/"+path
    existing=call("GET",endpoint,params={"ref":branch})
    if existing.status_code==200:
        if base64.b64decode(existing.json()["content"])!=raw:
            raise RuntimeError("existing result differs; refusing overwrite")
    elif existing.status_code==404:
        if head!=revision: raise RuntimeError("unexpected branch head; refusing write")
        written=call("PUT",endpoint,json={"message":"Archive verified synthetic v0.8.4 Colab summary","content":base64.b64encode(raw).decode(),"branch":branch})
        require(written,{201,409,422})
    else:
        require(existing,{200,404})
    # Verify remote bytes, including after a concurrent write or retried publication.
    remote=require(call("GET",endpoint,params={"ref":branch}),{200}).json()
    if base64.b64decode(remote["content"])!=raw:
        raise RuntimeError("remote verification mismatch")
    return {"branch":branch,"sha256":digest(raw),"url":f"https://github.com/{REPO}/blob/{branch}/{path}"}
