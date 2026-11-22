"""Investigation tools the agent can call. Each returns (result_for_model, short_finding_for_user).
Network failures never raise: they return an 'unavailable' result."""
import ipaddress
from functools import lru_cache
import re
import socket
from datetime import datetime, timezone
from typing import Tuple
from urllib.parse import urlparse

import httpx

TIMEOUT = 6


@lru_cache(maxsize=512)  # same domains repeat across an inbox scan
def check_domain(domain: str) -> Tuple[dict, str]:
    """DNS resolution and registration age (RDAP). Young domains are a strong scam signal."""
    domain = domain.strip().lower()
    # Models often pass a full email or URL; reduce it to the host.
    if "://" in domain:
        domain = urlparse(domain).hostname or ""
    domain = domain.rsplit("@", 1)[-1].split("/", 1)[0].removeprefix("www.")
    if not re.fullmatch(r"[a-z0-9.-]{3,253}", domain) or "." not in domain:
        return {"error": "invalid domain"}, f"{domain}: not a valid domain"
    info: dict = {"domain": domain}
    try:
        socket.getaddrinfo(domain, 443)
        info["resolves"] = True
    except OSError:
        info["resolves"] = False
    try:
        r = httpx.get(f"https://rdap.org/domain/{domain}", timeout=TIMEOUT, follow_redirects=True)
        if r.status_code == 200:
            for e in r.json().get("events", []):
                if e.get("eventAction") == "registration":
                    created = datetime.fromisoformat(e["eventDate"].replace("Z", "+00:00"))
                    info["age_days"] = (datetime.now(timezone.utc) - created).days
    except (httpx.HTTPError, ValueError, KeyError):
        pass
    parts = [f"{domain}:", "resolves" if info["resolves"] else "does NOT resolve"]
    parts.append(f"registered {info['age_days']} days ago" if "age_days" in info else "age unknown")
    return info, " ".join(parts[:2]) + ", " + parts[2]


def _public_host(host: str) -> bool:
    try:
        return all(ipaddress.ip_address(a[4][0]).is_global for a in socket.getaddrinfo(host, None))
    except (OSError, ValueError):
        return False


def fetch_page(url: str) -> Tuple[dict, str]:
    """Fetch a public web page as text (SSRF-guarded, no redirects, size-capped)."""
    u = urlparse(url.strip())
    if u.scheme not in ("http", "https") or not u.hostname:
        return {"error": "only http(s) URLs"}, "Skipped: not an http(s) URL"
    if not _public_host(u.hostname):
        return {"error": "blocked host"}, f"Skipped: {u.hostname} is not a public host"
    try:
        r = httpx.get(url, timeout=TIMEOUT, follow_redirects=False,
                      headers={"User-Agent": "TrustPathBot/0.1"})
    except httpx.HTTPError:
        return {"error": "unreachable"}, f"{u.hostname}: could not be fetched"
    if 300 <= r.status_code < 400:
        return {"redirect_to": r.headers.get("location", "")[:200]}, f"{u.hostname}: redirects elsewhere"
    text = re.sub(r"\s+", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>|<[^>]+>", " ", r.text[:200_000], flags=re.S))
    return ({"status": r.status_code, "text": text[:3000]},
            f"{u.hostname}: HTTP {r.status_code}, read {min(len(text), 3000)} characters")


TOOLS = {"check_domain": check_domain, "fetch_page": fetch_page}

SCHEMAS = [
    {"type": "function", "function": {
        "name": "check_domain",
        "description": "Check a domain's DNS resolution and registration age. Use on recruiter email domains and company websites found in the posting.",
        "parameters": {"type": "object", "properties": {"domain": {"type": "string"}}, "required": ["domain"]}}},
    {"type": "function", "function": {
        "name": "fetch_page",
        "description": "Fetch the text of a public web page (e.g. the job link or the company's careers page) to compare it with the posting.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
]
