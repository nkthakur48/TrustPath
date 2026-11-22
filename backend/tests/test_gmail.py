import base64

from fastapi.testclient import TestClient

from app.main import app
from app.services import gmail, tools

client = TestClient(app)


def _email(i, name, addr, subject, body):
    return {"id": i, "from_name": name, "from_email": addr, "subject": subject, "date": "", "snippet": body[:50], "body": body}


def test_not_configured_503(monkeypatch):
    monkeypatch.setattr(gmail.settings, "GOOGLE_CLIENT_ID", "")
    assert client.get("/api/v1/gmail/auth-url").status_code == 503


def test_auth_url_sets_state(monkeypatch):
    monkeypatch.setattr(gmail.settings, "GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setattr(gmail.settings, "GOOGLE_CLIENT_SECRET", "sec")
    r = client.get("/api/v1/gmail/auth-url")
    assert "gmail.readonly" in r.json()["url"] and "tp_state" in r.cookies


def test_callback_rejects_bad_state():
    r = client.get("/api/v1/gmail/callback?code=x&state=wrong", follow_redirects=False)
    assert r.headers["location"].endswith("gmail=error")


def test_scan_requires_session():
    assert TestClient(app).post("/api/v1/gmail/scan").status_code == 401


def test_scan_ranks_riskiest_first(monkeypatch):
    monkeypatch.setattr(tools, "check_domain", lambda d: ({"resolves": True, "age_days": 3000}, "ok"))
    sid = "s1"
    gmail._sessions[sid] = {"token": "t", "exp": 9e12}
    emails = [
        _email("1", "IBM Talent", "talent@ibm.com", "Backend Engineer role",
               "We are hiring a backend engineer. You will build Python services and review code. " * 4),
        _email("2", "HR Desk", "hr@gmail.com", "Job offer", "Urgent! Pay a registration fee on WhatsApp. Send Aadhaar."),
    ]
    monkeypatch.setattr(gmail, "list_job_emails", lambda token: emails)
    c = TestClient(app, cookies={"tp_session": sid})
    out = c.post("/api/v1/gmail/scan").json()
    assert [o["id"] for o in out] == ["2", "1"]
    assert out[0]["verdict"] in ("fake", "suspicious") and out[0]["red_flags"]


def test_body_decoding():
    data = base64.urlsafe_b64encode(b"hello world").decode()
    assert gmail._body({"mimeType": "text/plain", "body": {"data": data}}) == "hello world"
