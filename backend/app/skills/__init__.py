"""Detection skills. Each skill owns one of the five checks and is run by its own
LangGraph agent node. Check skills are pure functions of the request: no I/O, no globals
mutated. domain_intel is the one tool-using skill and runs in its own node."""

from collections import OrderedDict

from app.skills import (
    communication_channel,
    company_identity,
    hiring_process,
    posting_integrity,
    recruiter_verification,
)
from app.skills.base import RuleHit, Skill, SkillResult

SKILLS = OrderedDict(
    (skill.check_id, skill)
    for skill in (
        company_identity.SKILL,
        posting_integrity.SKILL,
        recruiter_verification.SKILL,
        communication_channel.SKILL,
        hiring_process.SKILL,
    )
)

__all__ = ["SKILLS", "RuleHit", "Skill", "SkillResult"]
