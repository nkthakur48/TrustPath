import re

from app.schemas.analyze import AnalyzeRequest
from app.skills.base import RuleHit, Skill, SkillResult, finalize, first_match
from app.skills.patterns import INTERVIEW_STEP, OVERPAYMENT, PAYMENT, SENSITIVE_REQUEST


def run(req: AnalyzeRequest) -> SkillResult:
    text = req.description
    hits, greens = [], []

    payment = first_match(PAYMENT, text)
    if payment:
        hits.append(RuleHit("process.payment", 40, "fail", f"Upfront payment requested (“{payment}”)", hard=True))

    sensitive = first_match(SENSITIVE_REQUEST, text)
    if sensitive:
        hits.append(RuleHit("process.sensitive_data", 30, "fail", f"Asks for identity or bank documents early (“{sensitive}”)", hard=True))

    overpayment = first_match(OVERPAYMENT, text)
    if overpayment:
        hits.append(RuleHit("process.overpayment", 30, "fail", f"Cheque or overpayment scheme (“{overpayment}”)", hard=True))

    if not hits and re.search(INTERVIEW_STEP, text, re.IGNORECASE):
        greens.append("Mentions an interview step")

    return finalize("process", hits, greens, clean_note="No payment or document requests found")


SKILL = Skill(
    check_id="process",
    description="Hiring process: upfront fees, early sensitive-document requests, and overpayment schemes (the safety floor).",
    run=run,
)
