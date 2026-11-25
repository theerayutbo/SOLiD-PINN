import base64
import json
import pytest
import publish_colab_uq as p

def fixture():
    q=[[20,8,10,.7],[25,12,15,.8],[30,16,20,.9]]
    v=[[0,0],[100,300],[200,600]]
    rep=[dict(design=a,noise=n,prior=k,quantiles=q,pred_quantiles=v,acceptance=.8) for a in p.DESIGNS for n in (1,5) for k in ("uniform","log_j0")]
    checks=[dict(design=a,noise=n,coarse=q,fine=q) for a in p.DESIGNS for n in (1,5)]
    cov=[dict(design=a,seed=s,quantiles=q,pred_quantiles=v) for a in p.DESIGNS for s in range(100,130)]
    return dict(truth=p.TRUTH,parameters=["R0","Rinf","tau","j0"],n=151,draws=16000,repeats=30,coverage_noise_mv=5,representative_seed=11,environment=dict(python="test",numpy="test",scipy="test"),representative=rep,grid_checks=checks,coverage=cov,private="must not leak")

def build(d,monkeypatch):
    monkeypatch.setattr(p,"SOURCE_BLOB",p.git_blob(b"solver"))
    monkeypatch.setattr(p,"TEST_BLOB",p.git_blob(b"test"))
    return p.build_bundle(json.dumps(d).encode(),"a"*40,b"solver",b"test")

def test_complete_and_whitelist(monkeypatch):
    b=build(fixture(),monkeypatch)
    assert b["completed"]["total"]==108
    assert b["coverage"][0]["parameter_covered"]==[30]*4
    assert "must not leak" not in p.canonical(b).decode()
    assert "seed" not in b["coverage"][0]

def test_reject_missing_duplicate(monkeypatch):
    d=fixture();d["coverage"][-1]=d["coverage"][0]
    with pytest.raises(ValueError,match="incomplete"):build(d,monkeypatch)

def test_reject_changed_source():
    with pytest.raises(ValueError,match="source differs"):p.build_bundle(b"{}","a"*40,b"wrong",b"test")

def test_reject_invalid_quantile(monkeypatch):
    d=fixture();d["representative"][0]["quantiles"]=[[50,8,10,.7],[25,12,15,.8],[30,16,20,.9]]
    with pytest.raises(ValueError,match="unordered"):build(d,monkeypatch)

class Resp:
    def __init__(self,status,data=None):self.status_code=status;self.data=data
    def json(self):return self.data

class Fake:
    def __init__(self):self.head=None;self.content=None;self.writes=0
    def request(self,method,url,**kw):
        assert "dummy-token" not in url
        if "/git/ref/" in url:return Resp(200,{"object":{"sha":self.head}}) if self.head else Resp(404)
        if url.endswith("/git/refs"):
            self.head=kw["json"]["sha"];return Resp(201)
        if method=="GET":return Resp(200,{"content":self.content}) if self.content else Resp(404)
        self.content=kw["json"]["content"];self.head="b"*40;self.writes+=1;return Resp(201)

def test_publish_idempotent(monkeypatch):
    b=build(fixture(),monkeypatch);s=Fake()
    first=p.publish(b,"dummy-token",s)
    second=p.publish(b,"dummy-token",s)
    assert first==second and s.writes==1
    assert base64.b64decode(s.content)==p.canonical(b)
    s.content=base64.b64encode(b"other").decode()
    with pytest.raises(RuntimeError,match="refusing overwrite"):p.publish(b,"dummy-token",s)
