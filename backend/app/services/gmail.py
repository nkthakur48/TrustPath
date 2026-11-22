"""Read-only Gmail access via OAuth 2.0 (plain httpx, no Google SDK).
Tokens live in memory only; nothing from the mailbox is stored."""
import base64
import re
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from email.utils import parseaddr
from typing import Dict, List, Optional
from urllib.parse import urlencode

import httpx

from app.core.config import settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://gmail.googleapis.com/gmail/v1/users/me"
SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
# in:anywhere includes Spam, where scam emails usually land.
QUERY = ('(job OR hiring OR recruiter OR "job offer" OR "offer letter" OR interview OR vacancy '
         'OR "work from home" OR opportunity) newer_than:30d in:anywhere -in:sent -in:trash')

# ponytail: in-memory, single process; use Redis/DB + refresh tokens for multi-user deployments.
_sessions: Dict[str, dict] = {}


class GmailAuthError(Exception):
    pass


def configured() -> bool:
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def auth_url(state: str) -> str:
    return AUTH_URL + "?" + urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID, "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code", "scope": SCOPE, "state": state, "prompt": "consent"})


def create_session(code: str) -> str:
    r = httpx.post(TOKEN_URL, timeout=10, data={
        "code": code, "client_id": settings.GOOGLE_CLIENT_ID, "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI, "grant_type": "authorization_code"})
    r.raise_for_status()
    sid = secrets.token_urlsafe(32)
    d = r.json()
    _sessions[sid] = {"token": d["access_token"], "exp": time.time() + d.get("expires_in", 3600)}
    return sid


def token_for(sid: Optional[str]) -> str:
    s = _sessions.get(sid or "")
    if not s or s["exp"] < time.time():
        _sessions.pop(sid or "", None)
        raise GmailAuthError()
    return s["token"]


def end_session(sid: Optional[str]) -> None:
    _sessions.pop(sid or "", None)


def _body(payload: dict) -> str:
    """First text/plain part, else tag-stripped text/html."""
    def walk(p, mime):
        if p.get("mimeType") == mime and p.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(p["body"]["data"] + "==").decode("utf-8", "replace")
        for c in p.get("parts", []):
            if (t := walk(c, mime)):
                return t
        return ""
    text = walk(payload, "text/plain")
    if not text:
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>|<[^>]+>", " ", walk(payload, "text/html"), flags=re.S)
    return re.sub(r"\s+", " ", text).strip()[:3000]


def _message(client: httpx.Client, mid: str) -> dict:
    r = client.get(f"{API}/messages/{mid}", params={"format": "full"})
    r.raise_for_status()
    m = r.json()
    h = {x["name"].lower(): x["value"] for x in m["payload"].get("headers", [])}
    name, addr = parseaddr(h.get("from", ""))
    return {"id": mid, "from_name": name, "from_email": addr.lower(), "subject": h.get("subject", ""),
            "date": h.get("date", ""), "snippet": m.get("snippet", ""),
            "body": _body(m["payload"]) or m.get("snippet", "")}


def list_job_emails(token: str, limit: int = 20) -> List[dict]:
    try:
        with httpx.Client(headers={"Authorization": f"Bearer {token}"}, timeout=15) as c:
            r = c.get(f"{API}/messages", params={"q": QUERY, "maxResults": limit})
            if r.status_code == 401:
                raise GmailAuthError()
            r.raise_for_status()
            ids = [m["id"] for m in r.json().get("messages", [])]
            with ThreadPoolExecutor(8) as pool:
                return list(pool.map(lambda i: _message(c, i), ids))
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            raise GmailAuthError() from e
        raise
