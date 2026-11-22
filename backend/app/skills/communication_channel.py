from app.schemas.analyze import AnalyzeRequest
from app.skills.base import RuleHit, Skill, SkillResult, clean, finalize, first_match
from app.skills.patterns import MODERATED_SOURCES, OFF_PLATFORM_CONTACT, RISKY_SOURCES


def run(req: AnalyzeRequest) -> SkillResult:
    hits, greens = [], []
    source = clean(req.source).lower()

    if source in RISKY_SOURCES:
        hits.append(RuleHit("channel.risky_source", 30, "fail", f"Offer arrived via {req.source}, an unmoderated channel"))
    elif source in MODERATED_SOURCES:
        greens.append(f"Found on a moderated platform ({req.source})")

    off_platform = first_match(OFF_PLATFORM_CONTACT, req.description)
    if off_platform:
        hits.append(RuleHit("channel.off_platform", 25, "fail", f"Asks to continue on an off-platform app (“{off_platform}”)"))

    return finalize("channel", hits, greens, clean_note="No off-platform contact requests found")


SKILL = Skill(
    check_id="channel",
    description="Communication channel: unmoderated sources and requests to move to WhatsApp/Telegram/Signal.",
    run=run,
)
