"""Deterministic rules engine: runs every check skill and folds the results into one score.
Pure functions, no I/O."""

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple

from app.schemas.analyze import CHECK_IDS, AnalyzeRequest
from app.skills import SKILLS, SkillResult
from app.skills.domain_intel import DomainIntel

BASE_SCORE = 100


@dataclass(frozen=True)
class RulesOutcome:
    score: int
    results: Dict[str, SkillResult]
    signals: List[Tuple[str, str]]  # (red|green, text)
    hard_rules: List[str]
    caps_verdict: bool


def run_skills(req: AnalyzeRequest) -> Dict[str, SkillResult]:
    return {check_id: skill.run(req) for check_id, skill in SKILLS.items()}


def combine(results: Mapping[str, SkillResult], domain: Optional[DomainIntel] = None) -> RulesOutcome:
    ordered = {check_id: results[check_id] for check_id in CHECK_IDS}
    if domain is not None:
        ordered["recruiter"] = ordered["recruiter"].extend(domain.hits, domain.greens)

    hits = [hit for result in ordered.values() for hit in result.hits]
    signals = [("red", hit.text) for hit in hits]
    signals += [("green", text) for result in ordered.values() for text in result.greens]
    if not hits and not signals:
        signals.append(("green", "No fraud patterns found in the posting text"))

    return RulesOutcome(
        score=max(0, min(100, BASE_SCORE - sum(hit.penalty for hit in hits))),
        results=ordered,
        signals=signals,
        hard_rules=[hit.rule for hit in hits if hit.hard],
        caps_verdict=any(hit.caps_verdict for hit in hits),
    )


def evaluate(req: AnalyzeRequest, domain: Optional[DomainIntel] = None) -> RulesOutcome:
    return combine(run_skills(req), domain)
