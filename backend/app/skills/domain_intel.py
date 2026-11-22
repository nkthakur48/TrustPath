"""Recruiter-domain investigation. Unlike the five check skills this one does network I/O
(through tools.check_domain), so it runs as its own graph node and never raises."""

from dataclasses import dataclass
from typing import Optional, Tuple

from app.schemas.analyze import AnalyzeRequest, TrailStep
from app.services import tools
from app.skills.base import RuleHit
from app.skills.domains import email_domain
from app.skills.patterns import FREE_EMAIL_DOMAINS

YOUNG_DOMAIN_DAYS = 180
ESTABLISHED_DOMAIN_DAYS = 730


@dataclass(frozen=True)
class DomainIntel:
    step: TrailStep
    hits: Tuple[RuleHit, ...] = ()
    greens: Tuple[str, ...] = ()

    @property
    def evidence(self) -> str:
        return self.step.finding


def investigate(req: AnalyzeRequest) -> Optional[DomainIntel]:
    domain = email_domain(req.recruiter_email)
    if not domain or domain in FREE_EMAIL_DOMAINS:
        return None

    info, finding = tools.check_domain(domain)
    hits, greens = [], []
    age = info.get("age_days")
    if info.get("resolves") is False:
        hits.append(RuleHit("recruiter.domain_dead", 25, "fail", "Recruiter email domain does not resolve"))
    elif age is not None and age < YOUNG_DOMAIN_DAYS:
        hits.append(RuleHit("recruiter.domain_young", 25, "fail", f"Recruiter domain was registered only {age} days ago"))
    elif age is not None and age > ESTABLISHED_DOMAIN_DAYS:
        greens.append(f"Recruiter domain is established ({age // 365}+ years old)")

    return DomainIntel(
        step=TrailStep(tool="check_domain", input=domain, finding=finding),
        hits=tuple(hits),
        greens=tuple(greens),
    )
