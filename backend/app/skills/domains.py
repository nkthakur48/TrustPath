import re
from difflib import SequenceMatcher
from typing import Optional

from app.skills.patterns import COMPANY_NAME_NOISE, JOB_AFFIXES, KNOWN_BRANDS

_SECOND_LEVEL = {"co", "com", "org", "net", "ac", "gov", "edu"}
_EMAIL_RE = re.compile(r"^[^@\s]+@([a-z0-9-]+\.)+[a-z]{2,}$", re.IGNORECASE)


def email_domain(email: Optional[str]) -> Optional[str]:
    if not email or not _EMAIL_RE.match(email.strip()):
        return None
    return email.strip().rsplit("@", 1)[1].lower()


def registered_root(domain: str) -> str:
    """'careers.stripe.com' -> 'stripe', 'acme.co.in' -> 'acme'."""
    parts = domain.lower().split(".")
    if len(parts) >= 3 and parts[-2] in _SECOND_LEVEL:
        return parts[-3]
    return parts[-2] if len(parts) >= 2 else parts[0]


def company_token(company: Optional[str]) -> Optional[str]:
    if not company:
        return None
    token = re.sub(COMPANY_NAME_NOISE, "", company.lower())
    token = re.sub(r"[^a-z0-9]", "", token)
    return token or None


def matches_company(domain: str, company: Optional[str]) -> bool:
    token = company_token(company)
    return bool(token) and registered_root(domain).replace("-", "") == token


def lookalike_of(domain: str, company: Optional[str]) -> Optional[str]:
    """Return the brand/company name that `domain` imitates, or None."""
    root = registered_root(domain)
    flat = root.replace("-", "").replace("_", "")
    tokens = [t for t in re.split(r"[-_]", root) if t]

    candidates = set(KNOWN_BRANDS)
    token = company_token(company)
    if token:
        candidates.add(token)

    for name in candidates:
        if flat == name:
            continue
        if len(name) >= 3 and len(tokens) > 1 and name in tokens:
            return name
        if len(name) >= 4 and any(flat in (affix + name, name + affix) for affix in JOB_AFFIXES):
            return name
        if len(name) >= 5 and abs(len(flat) - len(name)) <= 2 and SequenceMatcher(None, flat, name).ratio() >= 0.8:
            return name
    return None
