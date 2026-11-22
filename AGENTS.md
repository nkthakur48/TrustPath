# AGENTS.md: project rules for AI agents

Read this first. Source slides are in `judging_rules/` (photos). Slides 2 and 3 below are binding for every decision in this project.

## Hackathon deliverables (judging_rules_2.jpeg)
Four deliverables; **missing a required one risks disqualification. No changes or resubmissions once submitted.**
1. Video demo: the prototype in action (required).
2. Problem & Solution: the problem solved (required). File: `docs/SUBMISSION.md`.
3. IBM Bob usage: how IBM Bob was used (required). Keep a running log in `docs/SUBMISSION.md`; record every task where Bob did the work.
4. Code repository link (optional; we provide it).

## Judging criteria (judging_rules_3.jpeg), 4 x 5 pts = 20
| Criterion | What wins points | What it means here |
|-----------|------------------|--------------------|
| Completeness & Feasibility | Complete, feasible, **clear IBM tech use** | End-to-end flow works with no mock code; IBM Bob use is explicit and documented |
| Creativity & Innovation | Original, differentiated use of AI | **Agentic** investigation: the AI chooses tools (domain age, page fetch), shows its trail, and drafts actions for the user |
| Design & Usability | Great UX, easy for real users | Fast, clear verdict, plain-language next steps, visible errors, mobile-friendly |
| Effectiveness & Efficiency | Solves a priority problem, can scale | Real fraud patterns; rules-first (cheap) with LLM only where it adds value; stateless API |

Other rules: original work only, IBM Bob / watsonx must be used to be prize-eligible, one submission per team. Bonus: Most Creative Video Challenge (post video, tag IBM).

## Engineering rules that follow from this
- Product direction: consumer-facing **agentic** AI. Prefer an agent that investigates and acts (tool calls, evidence trail, drafted messages) over a single classify-this-text call. All LLM calls go through OpenRouter (`backend/app/services/openrouter.py`).
- Gmail scan is read-only, in-memory tokens, no mailbox content stored or sent to an LLM during triage.
- No mock logic, fake metrics, or unmeasured accuracy claims anywhere (feasibility and honesty).
- The demo must never break: every AI/network step degrades gracefully to rules-only.
- Secrets only in `backend/.env` (git-ignored). Never in frontend or git.
- Keep changes minimal and tested; `cd backend && pytest` must pass offline.
- Detailed plan: `docs/IMPLEMENTATION_PLAN.md`.
