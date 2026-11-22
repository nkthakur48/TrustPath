from app.schemas.analyze import AnalyzeRequest
from app.skills.base import RuleHit, Skill, SkillResult, clean, finalize
from app.skills.domains import company_token, email_domain, matches_company
from app.skills.patterns import FREE_EMAIL_DOMAINS, KNOWN_BRANDS

# ponytail: text-only. Real verification needs business registries; domain age is checked by domain_intel.
NOTE_UNVERIFIED = "Not verified against a registry"


def run(req: AnalyzeRequest) -> SkillResult:
    hits, greens = [], []
    company = clean(req.company)

    if not company:
        hits.append(RuleHit("company.missing", 10, "warn", "Company name not provided", caps_verdict=False))
    else:
        domain = email_domain(req.recruiter_email)
        if domain and matches_company(domain, company):
            greens.append(f"Recruiter email domain matches {company}")
        elif domain in FREE_EMAIL_DOMAINS and company_token(company) in KNOWN_BRANDS:
            # Status-only: the free-email penalty is already charged by the recruiter skill.
            hits.append(RuleHit("company.brand_impersonation", 0, "fail",
                                f"Claims to be {company} but contacts you from a personal {domain} address"))

    return finalize("company", hits, greens, clean_note=NOTE_UNVERIFIED)


SKILL = Skill(
    check_id="company",
    description="Company identity: is a company named, and does its stated identity line up with the contact details?",
    run=run,
)
