import re

from app.schemas.analyze import AnalyzeRequest
from app.skills.base import RuleHit, Skill, SkillResult, finalize, first_match
from app.skills.patterns import MIN_DESCRIPTION_CHARS, STRUCTURE_GREENS, TOO_GOOD, URGENCY


def run(req: AnalyzeRequest) -> SkillResult:
    text = req.description
    hits, greens = [], []

    urgency = first_match(URGENCY, text)
    if urgency:
        hits.append(RuleHit("posting.urgency", 10, "warn", f"Pressure language: “{urgency}”"))

    too_good = first_match(TOO_GOOD, text)
    if too_good:
        hits.append(RuleHit("posting.too_good", 15, "warn", f"Too-good-to-be-true pay claim: “{too_good}”"))

    if len(text) < MIN_DESCRIPTION_CHARS and not re.search(r"responsibilit", text, re.IGNORECASE):
        hits.append(RuleHit("posting.vague", 10, "warn", "Description is very short and lists no responsibilities"))

    for label, pattern in STRUCTURE_GREENS.items():
        if re.search(pattern, text, re.IGNORECASE):
            greens.append(label)

    return finalize("posting", hits, greens, clean_note="Specific and free of common scam language")


SKILL = Skill(
    check_id="posting",
    description="Job posting integrity: urgency, unrealistic pay, and vague descriptions.",
    run=run,
)
