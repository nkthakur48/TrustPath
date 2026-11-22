# TrustPath AI: Submission

## 1. Problem and solution

**Problem.** Roughly 1 in 7 online job postings is fraudulent (figure from product copy; no source cited). Candidates lose money (registration fees, "equipment" deposits, overpayment cheques) and identity data (Aadhaar, PAN, SSN). Scams move to WhatsApp and personal email, impersonate real companies, and use lookalike domains, so platform moderation alone does not protect the candidate.

**Solution.** TrustPath is a consumer-facing fraud-checking agent. A job seeker pastes a posting and gets a **Real / Suspicious / Fake** verdict, a 0-100 trust score, five independent checks (company, posting, recruiter, channel, hiring process), the evidence behind it, plain-language next steps, and a ready-to-send message to verify the recruiter.

A legitimate company can have a fake posting impersonating it, so TrustPath scores five dimensions independently rather than checking the company alone.

## 2. How it works

```
React UI ──POST /api/v1/analyze──> FastAPI
                                    │
              1. Rules engine       (payment/ID/overpayment language, channel, free-email, lookalike domains)
              2. Domain check tool  (DNS + registration age via RDAP) on the recruiter's domain
              3. AI agent           (OpenRouter, tool calling: check_domain, fetch_page; up to 4 rounds)
              4. Merge + safety floor
                                    │
              verdict, trust score, 5 checks, signals, investigation trail, next steps, draft message
```

- **Gmail scan.** One click on the home page connects Gmail (read-only OAuth) and ranks the user's job-related emails, Spam included, by fraud risk. The triage uses rules and domain age only (no mailbox content goes to an LLM); the user can send any email to the full agent. Tokens stay in memory and nothing is stored.
- **Agentic.** The model decides which tools to call (domain age, fetching the job link or careers page), and the UI shows the investigation trail. It also drafts the verification message for the user.
- **Rules first, AI where it adds value.** Rules are free, instant and explainable. The LLM adds semantic judgement and can only make a result *more* suspicious; it cannot relax a rules failure.
- **Safety floor.** Postings that ask for upfront payment, ID/bank details, or use overpayment language can never be returned as "real", whatever the model says. This also blunts prompt injection from the posting text.
- **Graceful degradation.** No API key or an OpenRouter failure falls back to rules plus the domain check; the demo never breaks.
- **Safe tools.** Page fetching blocks non-public hosts and redirects, caps size, and treats fetched text as untrusted data.
- **Scales cheaply.** Stateless API, one LLM call per posting (plus tool rounds), no stored postings.

## 3. How IBM Bob was used

IBM Bob was used in a separate session to produce the project's **planning, architecture and code**. Bob's output was the starting point for this repository.

| Area | What IBM Bob did | Evidence |
|------|------------------|----------|
| Planning | Product and implementation planning | TODO: link/screenshot of the Bob session |
| Architecture | System design (frontend, API, detection approach) | TODO |
| Code | Code generated in the Bob session | TODO: list files/commits |

> TODO (team): replace each TODO with a specific file, commit or screenshot. Judges can then verify the claim.

Additional tooling, disclosed for transparency: the agentic `/analyze` endpoint (rules engine, OpenRouter tool-calling agent, tests), the wiring of the React UI to it, and these docs were implemented in a later session with the pi coding agent, following `docs/IMPLEMENTATION_PLAN.md`. Runtime AI calls go through OpenRouter.

## 4. Limitations (be upfront)

- Company and recruiter checks are limited to domain age/DNS and what the agent can fetch. There is no business-registry or LinkedIn verification yet.
- Thresholds and penalties are hand-tuned. No labelled evaluation set, so **no accuracy figure is claimed**.
- A verdict is a risk signal, not proof. False positives and false negatives are possible; the UI says so.
- Posted text and recruiter emails are personal data; define retention and consent before a hosted launch (nothing is stored today).

## 5. Demo script (about 2 minutes)

1. (0:00) Hook: "1 in 7 job posts is a scam, and the victim is on their own." Show the home page.
2. (0:15) Paste **demo 1 (fake)**. Show the analysis steps, then the verdict, red signals, and the investigation trail (lookalike/dead domain).
3. (0:50) Paste **demo 2 (suspicious)**. Point out the mixed signals and the drafted message; click Copy.
4. (1:15) Paste **demo 3 (real)**. Show the established domain (`ibm.com`, decades old) and the green result.
5. (1:35) Say: rules first, AI agent where it helps, safety floor so the AI cannot wave a fee scam through, graceful fallback.
6. (1:50) Close: honest limits and next steps (registry checks, evaluation set). Mention how IBM Bob was used.

Record the video, post it on social media and tag IBM for the Most Creative Video Challenge.

## 6. Run it

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env            # add OPENROUTER_API_KEY (agent) and GOOGLE_CLIENT_ID/SECRET (Gmail scan)
.venv/bin/uvicorn app.main:app  # http://localhost:8000/docs
cd ../frontend && npm install && npm run dev   # proxies /api to :8000
```

Repository: https://github.com/nkthakur48/TrustPath
