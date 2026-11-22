from app.schemas.analyze import AnalyzeRequest
from app.services import rules, tools
from app.skills import SKILLS, domain_intel
from app.skills.domains import lookalike_of

CLEAN = (
    "Responsibilities: build and maintain the Dashboard in React and TypeScript, partner with design "
    "and backend teams, and own features end to end. Requirements: 5+ years of frontend experience, "
    "strong TypeScript, and experience with design systems. Interview process: recruiter screen, "
    "technical interview, and a team conversation. Benefits: health insurance, paid leave, and equity."
)
SCAM = (
    "Urgent! Work from home, earn Rs 5000/day, no experience. Pay Rs 2500 registration fee. "
    "Contact HR on WhatsApp. Send Aadhaar and PAN to confirm."
)


def _eval(**fields):
    fields.setdefault("description", CLEAN)
    fields.setdefault("company", "Stripe")
    return rules.evaluate(AnalyzeRequest(**fields))


def _fired(outcome):
    return {hit.rule for result in outcome.results.values() for hit in result.hits}


def test_skills_cover_five_checks_in_order():
    assert list(SKILLS) == ["company", "posting", "recruiter", "channel", "process"]


def test_clean_posting_scores_high():
    outcome = _eval(recruiter_email="jane@stripe.com", source="Company Website")
    assert outcome.score >= 75 and not _fired(outcome)


def test_blatant_scam_scores_low():
    outcome = _eval(description=SCAM, company="Amazon Careers", recruiter_email="amazon.hr@gmail.com", source="WhatsApp")
    assert outcome.score < 45
    assert {"process.payment", "process.sensitive_data"} <= set(outcome.hard_rules)


def test_channel_risky_source():
    for source in ("WhatsApp", "telegram", "Email"):
        outcome = _eval(source=source)
        assert "channel.risky_source" in _fired(outcome)
        assert outcome.results["channel"].status == "fail"


def test_channel_off_platform_request():
    assert "channel.off_platform" in _fired(_eval(description=CLEAN + " For next steps, message us on Telegram."))


def test_recruiter_free_email():
    outcome = _eval(recruiter_email="stripe.hr@gmail.com")
    assert "recruiter.free_email" in _fired(outcome)
    assert outcome.results["recruiter"].status == "warn"


def test_recruiter_lookalike_domain():
    outcome = _eval(recruiter_email="hr@careers-stripe.com")
    assert "recruiter.lookalike" in _fired(outcome)
    assert outcome.results["recruiter"].status == "fail"


def test_lookalike_detection():
    assert lookalike_of("careers-stripe.com", "Stripe") == "stripe"
    assert lookalike_of("stripecareers.net", "Stripe") == "stripe"
    assert lookalike_of("amaz0n.com", "") == "amazon"
    assert lookalike_of("stripe.com", "Stripe") is None
    assert lookalike_of("metaverselabs.com", "Metaverse Labs") is None
    assert lookalike_of("acme.co.in", "Acme Pvt Ltd") is None


def test_process_payment():
    outcome = _eval(description=CLEAN + " Selected candidates must pay a refundable deposit of Rs 3000.")
    assert "process.payment" in outcome.hard_rules


def test_salary_direct_deposit_is_not_payment():
    assert "process.payment" not in _fired(_eval(description=CLEAN + " Salary is paid by direct deposit monthly."))


def test_process_sensitive_data():
    outcome = _eval(description=CLEAN + " Please share your Aadhaar and bank details to proceed.")
    assert "process.sensitive_data" in outcome.hard_rules


def test_process_overpayment():
    outcome = _eval(description=CLEAN + " We will send a cheque; deposit it and send back the rest.")
    assert "process.overpayment" in outcome.hard_rules


def test_posting_urgency_only():
    outcome = _eval(description=CLEAN + " Urgent requirement.")
    assert _fired(outcome) == {"posting.urgency"}
    assert outcome.score == 90


def test_posting_too_good():
    assert "posting.too_good" in _fired(_eval(description=CLEAN + " Earn up to $500 per day."))


def test_posting_vague():
    assert "posting.vague" in _fired(_eval(description="Hiring now. Good pay. DM for details."))


def test_brand_with_personal_email_fails_company():
    outcome = _eval(company="Amazon Careers", recruiter_email="amazon.hr.jobs@gmail.com")
    assert outcome.results["company"].status == "fail"
    assert _eval(company="Acme", recruiter_email="acme.hr@gmail.com").results["company"].status == "pass"


def test_company_missing_does_not_cap_verdict():
    outcome = _eval(company="")
    assert "company.missing" in _fired(outcome)
    assert outcome.caps_verdict is False


def test_recruiter_note_uses_worst_finding():
    intel = domain_intel.DomainIntel(
        step=None,
        hits=(domain_intel.RuleHit("recruiter.domain_young", 25, "fail", "Registered 5 days ago"),),
    )
    outcome = rules.combine(rules.run_skills(AnalyzeRequest(description=CLEAN, company="Acme", recruiter_email="hr@acme.com")), intel)
    assert outcome.results["recruiter"].status == "fail"
    assert outcome.results["recruiter"].note == "Registered 5 days ago"


def test_domain_intel_skips_free_email(monkeypatch):
    called = []
    monkeypatch.setattr(tools, "check_domain", lambda d: called.append(d) or ({}, ""))
    assert domain_intel.investigate(AnalyzeRequest(description=CLEAN, recruiter_email="x@gmail.com")) is None
    assert domain_intel.investigate(AnalyzeRequest(description=CLEAN, recruiter_email="not an email")) is None
    assert called == []


_REAL_CHECK_DOMAIN = tools.check_domain


def test_check_domain_accepts_email_and_url(monkeypatch):
    monkeypatch.setattr(tools.socket, "getaddrinfo", lambda *a, **k: [])
    monkeypatch.setattr(tools.httpx, "get", lambda *a, **k: (_ for _ in ()).throw(tools.httpx.ConnectError("offline")))
    for value in ("jane.doe@stripe.com", "https://www.stripe.com/jobs/123", "WWW.Stripe.com"):
        info, _ = _REAL_CHECK_DOMAIN(value)
        assert info.get("domain") == "stripe.com", value


def test_domain_intel_flags_dead_and_young_domains(monkeypatch):
    req = AnalyzeRequest(description=CLEAN, recruiter_email="hr@acme.com")
    monkeypatch.setattr(tools, "check_domain", lambda d: ({"resolves": False}, f"{d}: dead"))
    assert domain_intel.investigate(req).hits[0].rule == "recruiter.domain_dead"
    monkeypatch.setattr(tools, "check_domain", lambda d: ({"resolves": True, "age_days": 10}, f"{d}: new"))
    assert domain_intel.investigate(req).hits[0].rule == "recruiter.domain_young"
