"""LangGraph orchestration for job-posting analysis.

START ─┬─ company_agent ───────────────┐
       ├─ posting_agent ───────────────┤
       ├─ recruiter_agent ─────────────┤
       ├─ channel_agent ───────────────┼─ merge ─ END
       ├─ process_agent ───────────────┤
       └─ domain_check ─ investigator ─┘

*_agent: one deterministic skill each (app.skills), run in parallel.
domain_check: looks up the recruiter's domain; its finding is handed to the investigator as evidence.
investigator: the OpenRouter tool-calling agent. Yields nothing when the key is missing or any
call fails, so the graph always completes on rules alone.
"""

import logging
import operator
from functools import lru_cache
from typing import Annotated, Dict, List, Optional

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, TrailStep
from app.services import analyzer, openrouter, rules
from app.services.openrouter import LLMOut
from app.skills import SKILLS, Skill, SkillResult, domain_intel
from app.skills.domain_intel import DomainIntel

logger = logging.getLogger(__name__)


class AnalysisState(TypedDict, total=False):
    request: AnalyzeRequest
    skill_results: Annotated[Dict[str, SkillResult], operator.or_]
    domain: Optional[DomainIntel]
    agent: Optional[LLMOut]
    trail: Annotated[List[TrailStep], operator.add]
    response: AnalyzeResponse


def _agent_for(skill: Skill):
    def agent(state: AnalysisState) -> dict:
        return {"skill_results": {skill.check_id: skill.run(state["request"])}}

    agent.__name__ = f"{skill.check_id}_agent"
    return agent


def domain_check(state: AnalysisState) -> dict:
    try:
        intel = domain_intel.investigate(state["request"])
    except Exception as exc:  # noqa: BLE001 - tools never raise, but the demo must not break
        logger.warning("domain_check failed: %s", type(exc).__name__)
        intel = None
    return {"domain": intel, "trail": [intel.step] if intel else []}


def investigator(state: AnalysisState) -> dict:
    intel = state.get("domain")
    try:
        outcome = openrouter.run_agent(state["request"], intel.evidence if intel else "")
    except Exception as exc:  # noqa: BLE001
        logger.warning("investigator failed: %s", type(exc).__name__)
        outcome = None
    if not outcome:
        return {"agent": None, "trail": []}
    llm, agent_trail = outcome
    return {"agent": llm, "trail": list(agent_trail)}


def merge(state: AnalysisState) -> dict:
    outcome = rules.combine(state["skill_results"], state.get("domain"))
    return {"response": analyzer.merge(outcome, state.get("agent"), state.get("trail", []))}


def build_analysis_graph():
    builder = StateGraph(AnalysisState)
    waits_for = []
    for skill in SKILLS.values():
        name = f"{skill.check_id}_agent"
        builder.add_node(name, _agent_for(skill))
        builder.add_edge(START, name)
        waits_for.append(name)

    builder.add_node("domain_check", domain_check)
    builder.add_node("investigator", investigator)
    builder.add_node("merge", merge)
    builder.add_edge(START, "domain_check")
    builder.add_edge("domain_check", "investigator")
    waits_for.append("investigator")

    builder.add_edge(waits_for, "merge")
    builder.add_edge("merge", END)
    return builder.compile()


@lru_cache
def get_analysis_graph():
    return build_analysis_graph()
