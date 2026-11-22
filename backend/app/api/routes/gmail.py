import secrets
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import httpx
from fastapi import APIRouter, Cookie, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.analyze import AnalyzeRequest
from app.services import analyzer, gmail

router = APIRouter(prefix="/gmail")
COOKIE = dict(httponly=True, samesite="lax", max_age=3600)  # ponytail: add secure=True behind HTTPS


class EmailResult(BaseModel):
    id: str
    from_name: str
    from_email: str
    subject: str
    date: str
    snippet: str
    description: str
    verdict: str
    trust_score: int
    red_flags: List[str]


@router.get("/auth-url")
def auth_url(response: Response) -> dict:
    if not gmail.configured():
        raise HTTPException(503, "Gmail is not configured on the server (missing GOOGLE_CLIENT_ID/SECRET).")
    state = secrets.token_urlsafe(16)
    response.set_cookie("tp_state", state, **COOKIE)
    return {"url": gmail.auth_url(state)}


@router.get("/callback")
def callback(code: str = "", state: str = "", error: str = "", tp_state: Optional[str] = Cookie(None)):
    ok = code and not error and tp_state and secrets.compare_digest(state, tp_state)
    try:
        sid = gmail.create_session(code) if ok else None
    except (httpx.HTTPError, KeyError):
        sid = None
    redirect = RedirectResponse(f"{settings.FRONTEND_URL}/?gmail={'connected' if sid else 'error'}")
    if sid:
        redirect.set_cookie("tp_session", sid, **COOKIE)
    redirect.delete_cookie("tp_state")
    return redirect


@router.post("/scan", response_model=List[EmailResult])
def scan(tp_session: Optional[str] = Cookie(None)) -> List[EmailResult]:
    """Triage recent job-related emails with rules + domain checks (no LLM: fast and cheap).
    Use /analyze on a single email for the full agent investigation."""
    try:
        emails = gmail.list_job_emails(gmail.token_for(tp_session))
    except gmail.GmailAuthError:
        raise HTTPException(401, "Gmail not connected or session expired.")
    except httpx.HTTPError:
        raise HTTPException(502, "Could not read Gmail.")

    def triage(e: dict) -> EmailResult:
        req = AnalyzeRequest(description=(e["body"] or e["subject"] or "(empty)")[:10000],
                             title=e["subject"][:200], company=e["from_name"][:200],
                             recruiter_email=e["from_email"][:200])
        r = analyzer.analyze(req, use_agent=False)
        return EmailResult(**{k: e[k] for k in ("id", "from_name", "from_email", "subject", "date", "snippet")},
                           description=req.description, verdict=r.verdict, trust_score=r.trust_score,
                           red_flags=[s.text for s in r.signals if s.type == "red"][:3])

    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(triage, emails))
    return sorted(results, key=lambda x: x.trust_score)  # riskiest first


@router.post("/disconnect", status_code=204)
def disconnect(response: Response, tp_session: Optional[str] = Cookie(None)) -> None:
    gmail.end_session(tp_session)
    response.delete_cookie("tp_session")
