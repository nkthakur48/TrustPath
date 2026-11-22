"""Merges the rules outcome with the optional agent investigation. Verdict thresholds live here only."""

from typing import List, Optional

from app.schemas.analyze import CHECK_IDS, CHECK_LABELS, AnalyzeRequest, AnalyzeResponse, Check, NextStep, Signal, TrailStep
from app.services.openrouter import LLMOut
from app.services.rules import RulesOutcome
from app.skills.base import STATUS_RANK

REAL_MIN_SCORE = 75
FAKE_MAX_SCORE = 44
RISK_ADJUSTMENT_MIN = -40
RISK_ADJUSTMENT_MAX = 10
MAX_SIGNALS = 8

COMPANY_UNVERIFIED_NOTE = "Not verified against a registry"
COMPANY_TEXT_ONLY_NOTE = "Based on posting text only; not checked against a registry"
AI_ESCALATED_NOTE = "Flagged by AI review"

STATIC_STEPS = {
    "fake": [("Do not apply or respond", "Engaging further risks financial loss or identity theft."),
             ("Report the posting", "Flag it on the platform where you found it."),
             ("Warn others", "Share this result to protect fellow job seekers.")],
    "suspicious": [("Verify via official channels", "Call the company using numbers from its official website."),
                   ("Check the recruiter on LinkedIn", "Confirm they work at the company."),
                   ("Never pay or share ID", "Do not send money or documents until identity is confirmed.")],
    "real": [("Apply via the official careers page", "Go to the company's own website, not a forwarded link."),
             ("Research the company", "Check the company's site and reviews."),
             ("Guard sensitive documents", "Do not share ID or bank details early.")],
}


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def verdict_for(score: int) -> str:
    if score >= REAL_MIN_SCORE:
        return "real"
    return "fake" if score <= FAKE_MAX_SCORE else "suspicious"


def _checks(rules: RulesOutcome, llm: Optional[LLMOut]) -> List[Check]:
    checks = []
    for check_id in CHECK_IDS:
        result = rules.results[check_id]
        status, note = result.status, result.note
        llm_status = llm.checks.get(check_id) if llm else None
        if llm_status and STATUS_RANK[llm_status] > STATUS_RANK[status]:  # may escalate, never relax
            status, note = llm_status, AI_ESCALATED_NOTE
        if check_id == "company" and status == "pass":
            # Rules alone can't vouch for a company; agreement with the agent is the most we claim.
            status, note = ("pass", COMPANY_TEXT_ONLY_NOTE) if llm else ("warn", COMPANY_UNVERIFIED_NOTE)
        checks.append(Check(id=check_id, label=CHECK_LABELS[check_id], status=status, note=note))
    return checks


def _signals(rules: RulesOutcome, llm: Optional[LLMOut]) -> List[Signal]:
    candidates = [Signal(type=t, text=x) for t, x in rules.signals] + (list(llm.signals) if llm else [])
    seen, unique = set(), []
    for signal in candidates:
        key = signal.text.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(signal)
    return unique[:MAX_SIGNALS]


def merge(rules: RulesOutcome, llm: Optional[LLMOut], trail: List[TrailStep]) -> AnalyzeResponse:
    score = rules.score
    if llm:
        score += clamp(llm.risk_adjustment, RISK_ADJUSTMENT_MIN, RISK_ADJUSTMENT_MAX)
    score = clamp(score, 0, 100)
    checks = _checks(rules, llm)

    # Safety floor: rules-detected payment/ID/overpayment can't be argued away by the agent.
    if len(rules.hard_rules) >= 2:
        score = min(score, FAKE_MAX_SCORE)
    elif rules.hard_rules or rules.caps_verdict or any(c.status == "fail" for c in checks):
        score = min(score, REAL_MIN_SCORE - 1)

    verdict = verdict_for(score)
    steps = list(llm.next_steps) if llm and llm.next_steps else [NextStep(title=t, detail=d) for t, d in STATIC_STEPS[verdict]]
    return AnalyzeResponse(
        verdict=verdict,
        trust_score=score,
        risk={"real": "low", "suspicious": "medium", "fake": "high"}[verdict],
        checks=checks,
        signals=_signals(rules, llm),
        next_steps=steps,
        engine="rules+agent" if llm else "rules",
        trail=trail,
        draft_message=llm.draft_message if llm else "",
    )


def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    from app.graph.analysis import get_analysis_graph

    return get_analysis_graph().invoke({"request": req})["response"]
