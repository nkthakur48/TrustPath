import re
from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional, Tuple

from app.schemas.analyze import AnalyzeRequest, Status

STATUS_RANK = {"pass": 0, "warn": 1, "fail": 2}


def worse(a: Status, b: Status) -> Status:
    return a if STATUS_RANK[a] >= STATUS_RANK[b] else b


def clean(value: Optional[str]) -> str:
    return (value or "").strip()


@dataclass(frozen=True)
class RuleHit:
    rule: str
    penalty: int
    status: Status
    text: str
    # Upfront payment, sensitive-data and overpayment rules form the safety floor.
    hard: bool = False
    # Informational hits (e.g. a missing company name) don't cap the verdict.
    caps_verdict: bool = True


@dataclass(frozen=True)
class SkillResult:
    check_id: str
    status: Status
    note: str
    hits: Tuple[RuleHit, ...] = ()
    greens: Tuple[str, ...] = ()

    @property
    def penalty(self) -> int:
        return sum(h.penalty for h in self.hits)

    def extend(self, hits: Iterable[RuleHit], greens: Iterable[str] = ()) -> "SkillResult":
        hits = tuple(hits)
        if not hits and not greens:
            return self
        merged = finalize(self.check_id, self.hits + hits, self.greens + tuple(greens), self.note, self.status)
        return merged


@dataclass(frozen=True)
class Skill:
    """A self-contained check that one LangGraph agent node runs."""

    check_id: str
    description: str
    run: Callable[[AnalyzeRequest], SkillResult] = field(repr=False)


def finalize(
    check_id: str,
    hits: Iterable[RuleHit],
    greens: Iterable[str],
    clean_note: str,
    clean_status: Status = "pass",
) -> SkillResult:
    hits = tuple(hits)
    status: Status = clean_status
    for hit in hits:
        status = worse(status, hit.status)
    worst = next((h for h in hits if h.status == status), None)
    return SkillResult(
        check_id=check_id,
        status=status,
        note=worst.text if worst else clean_note,
        hits=hits,
        greens=tuple(greens),
    )


def first_match(patterns: Iterable[str], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None
