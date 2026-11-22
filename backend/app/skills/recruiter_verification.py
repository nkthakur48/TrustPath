from app.schemas.analyze import AnalyzeRequest
from app.skills.base import RuleHit, Skill, SkillResult, clean, finalize
from app.skills.domains import email_domain, lookalike_of, matches_company
from app.skills.patterns import FREE_EMAIL_DOMAINS


def run(req: AnalyzeRequest) -> SkillResult:
    if not clean(req.recruiter_email):
        return finalize("recruiter", [], [], clean_note="No recruiter email provided; identity unverified", clean_status="warn")

    domain = email_domain(req.recruiter_email)
    if not domain:
        return finalize("recruiter", [], [], clean_note="Recruiter contact is not a valid email address", clean_status="warn")

    hits, greens = [], []
    if domain in FREE_EMAIL_DOMAINS:
        hits.append(RuleHit("recruiter.free_email", 20, "warn", f"Recruiter uses a personal email domain ({domain})"))
    else:
        imitated = lookalike_of(domain, req.company)
        if imitated:
            hits.append(RuleHit("recruiter.lookalike", 35, "fail", f"Recruiter domain {domain} imitates “{imitated}”"))
        elif matches_company(domain, req.company):
            greens.append("Recruiter email uses the company's own domain")

    # ponytail: no LinkedIn or company-directory lookup (ToS-restricted); domain heuristics plus domain_intel only.
    return finalize("recruiter", hits, greens, clean_note="Corporate email domain; person not individually verified")


SKILL = Skill(
    check_id="recruiter",
    description="Recruiter verification: personal email domains and lookalike/impersonating domains.",
    run=run,
)
