# Quality attributes — Budgets and spend summary

Derived from the requirements at `docs/sdlc/budgets7/04-requirements/requirements#114.md` (referred to below as BUD-n) and the solution concept at `docs/sdlc/budgets7/02-concept/solution_concept#89.md`. Bohdan's answer on thresholds (settled_question#110) was that **no latency number has been settled** and asked that a figure be proposed and marked unconfirmed rather than asserted. Every threshold below is therefore *proposed, not confirmed*, and each appears in `open_questions`.

Overlap was checked requirement by requirement before writing: none of BUD-1..BUD-11 fixes a number, so both attributes below add a dimension the functional set leaves open (a percentile over a load, a receipt-volume condition) rather than restating a requirement. On the category walk: performance and scalability are written below; availability, portability, usability, accessibility, observability and privacy are judged not to apply and say so; compliance was answered "none" (settled_question#111), which is on the record here.

## INV-NFR-1 — Summary and set latency

### Requirement

While the backend is under normal single-user load, the budgets API shall respond to a summary or set-budget request within the stated threshold.

### Rationale

The whole value of the feature is that the user does not do the arithmetic by hand (settled_question#71); a summary slow enough to abandon makes the feature no better than mental arithmetic. The figure is **proposed, not confirmed**: the receipts endpoints meet it informally at today's scale, and bohdan declined to settle a number (settled_question#110). The implementer and bohdan must confirm, or the acceptance test for this attribute has no decided value. This does not restate any BUD requirement — BUD-3 fixes *what* the summary returns, this bounds *how fast*.

### Measure

| | |
|---|---|
| metric | p95 response time for `POST /api/v1/budgets` and `GET /api/v1/budgets/{period}/summary` |
| threshold | 200 ms |
| conditions | 5 requests/second sustained over 5 minutes against the local SQLite backend with production-sized data for one user (a few thousand receipts), single authenticated user |

### Traces to

- [[concept-89/chosen-approach]] — summary computed on the fly at request time
- BUD-3 (bounds its response time; BUD-3 itself fixes only the content)

## INV-NFR-2 — On-the-fly summary scales with receipt volume

### Requirement

While the chosen design computes the summary on the fly from receipt rows at request time, the summary endpoint shall stay within the stated bound as one user's receipt count grows.

### Rationale

The concept names this explicitly as the risk that is expensive to walk back: no stored aggregates, so summary cost grows with receipt count (concept, "Risks"). At one user's scale it is judged negligible (settled_question#82) — this attribute makes that judgement testable instead of assumed. It adds a condition (receipt volume) that no functional requirement fixes. The figure is **proposed, not confirmed** by bohdan and the implementer.

### Measure

| | |
|---|---|
| metric | p95 response time for `GET /api/v1/budgets/{period}/summary` |
| threshold | 500 ms |
| conditions | with 10,000 receipts for the user spread across periods, on the local SQLite backend, measured over 100 requests |

### Traces to

- [[concept-89/risks]] — summary cost grows with receipt count
- [[concept-89/chosen-approach]] — no stored aggregates

## Categories considered and not written

- **Availability** — a single-user, single-process FastAPI + SQLite backend with no deployment change in scope; an uptime threshold would bind infrastructure this change does not touch. Not applicable.
- **Security** — BUD-8 and BUD-9 already fix the isolation and authentication behaviour testably; any attribute here would restate them. Not written; see `open_questions` if a penetration-style check is wanted later.
- **Privacy** — bohdan answered compliance "none" (settled_question#111); no data-residency or retention rule applies. Cross-user non-disclosure is already BUD-8.
- **Usability / accessibility** — API-only, frontend explicitly out of scope; nothing for a person to perceive directly.
- **Maintainability** — the concept records the change as fully reversible (settled_question#88: removing the router removes the feature). That is an inspection finding recorded in the concept, not a measurable attribute; a threshold with a digit would be invented decoration, so none is written.
- **Portability** — the stack is fixed by constraint (settled_question#86: FastAPI, SQLAlchemy, pytest as they stand; SQLite). No portability claim is in play.
- **Observability** — error handling is centralised in `create_app()` (`backend/app/main.py:47-62`) and the budgets router inherits it; no logging or metric requirement was asked for. If one is wanted, it is new scope, not an attribute of this change.
- **Compliance** — answered "none" by bohdan (settled_question#111); recorded here so the question shows as asked.
