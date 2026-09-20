# Quality attributes — Receipt photos on expenses

Attempt 4 of this artifact, re-issued against requirements attempt 4 (requirement#112), which resolved gate_finding#114. The capability/level division the finding endorsed stands and was checked line-by-line against the final requirement set in this run: RCP-3 states and tests the refusal-equivalence behaviour; INV-NFR-2 carries only the *completeness level* of that rule (all unauthorized cases, byte-identical, every CI pass). Nothing here restates a requirement's behaviour as its requirement sentence — INV-NFR-2's sentence is measure-shaped ("shall return the same refusal …" names the level only insofar as the measure defines it), and the finding's complaint is answered by RCP-16: the photo-URL shape is now settled in the requirement set itself, so the open question this document carried at attempt 3 is removed, not argued.

Two of this document's three prior open questions are now closed by requirement#112 and require no restatement here: the photo-serving URL shape (RCP-16 settles it — bytes only through the bearer-authenticated API, rendered client-side) and python-multipart (settled as a feature cost per solution_concept#87 and settled_question#84). One remains, with its fallback decided: the 5 MB limit against the 10-second TimeoutMiddleware, which bohdan bound to be tested against the deployed stack (settled_question#107).

Repository checks backing the claims, made in this run rather than asserted: backend/app/main.py:18 defines `REQUEST_TIMEOUT_SECONDS` defaulting to 10 with the `TimeoutMiddleware` class, and backend/requirements.txt lists fastapi, uvicorn[standard], sqlalchemy, psycopg2-binary, pytest, httpx, bcrypt, PyJWT and email-validator only — python-multipart is absent from the tracked requirements, so INV-NFR-4's threshold of "1 (python-multipart)" is a real, checkable constraint and not a description of the status quo.

Every numeric threshold comes from settled_question#107, which bohdan answered as *chosen, and binding* — none are invented. The same answer explicitly ruled several categories unmeasured: concurrent users (one), request volume (none), availability (runs on a laptop under docker compose) — those are on the record as not settled rather than written as fake targets.

Categories walked explicitly: performance (INV-NFR-1), availability (not settled, see below), security (INV-NFR-2), privacy (behaves like security here — retention carried by RCP-9, confidentiality by INV-NFR-2), usability (no threshold named anywhere in this run), accessibility (INV-NFR-3), maintainability (INV-NFR-4), portability (INV-NFR-5), scalability (explicitly excluded — one user), observability (not applicable at this scale), compliance (answered "none" in settled_question#108 — no artifact required, the answer is on the record).

## INV-NFR-1 — Photo open latency

### Requirement

While the backend runs under the existing 10-second TimeoutMiddleware, when the owner opens a receipt photo, the receipts service shall serve the stored photo in a response meeting the stated threshold.

### Rationale

The outcome someone would notice is that the photo opens again from the expense without a camera-roll hunt (settled_question#35). If opening is slow the feature exists but is not used. The 2-second figure is bohdan's binding threshold from settled_question#107 — proposed by the maker and therefore settled, not assumed.

### Measure

| | |
|---|---|
| metric | p95 response time for serving a stored receipt photo to its owner |
| threshold | 2000 ms |
| conditions | measured locally on the deployed compose stack, over at least 50 consecutive fetches of a photo at the 5 MB limit, after upload in a separate session |

### Traces to

- solution_concept#87 — chosen approach
- settled_question#107 — binding open threshold
- requirement#112 — RCP-2 (capability; this attribute carries the level)

## INV-NFR-2 — Photo confidentiality

### Requirement

While the receipts service is running, when any request for a receipt photo arrives without the owning user's authentication, the receipts service shall return the same refusal it gives for a nonexistent receipt id.

### Rationale

Must-have 3 is the one priority the maker will not trade: receipt photos routinely show card fragments, addresses and merchant detail (settled_question#108). The identical-refusal rule is RCP-3's; this attribute is the *measure* of that rule, not a restatement — the gate finding flagged exactly this drift, and the division is now: RCP-3 states and tests the behaviour, this states the completeness level (all unauthorized cases, byte-identical, on every CI pass) it must hold at. Category is security, not privacy: the control is authorization at the endpoint, which RCP-16 guarantees is the only serving route, and the admin role grants nothing here (settled_question#110).

### Measure

| | |
|---|---|
| metric | proportion of unauthorized photo requests (other user, admin, unauthenticated) returning byte-identical not-found responses to the nonexistent-id case |
| threshold | 100% |
| conditions | automated test suite exercising all three unauthorized cases against every photo-serving route, run on every CI pass |

### Traces to

- settled_question#106 — must-have 3
- settled_question#108 — personal financial documents
- settled_question#109 — refusal equivalence rule
- requirement#112 — RCP-3 (behaviour) and RCP-16 (authenticated serving is the only route)

## INV-NFR-3 — Screen-reader access to the photo viewer

### Requirement

Where the receipt screen displays an attached photo, the frontend shall render that photo with alt text naming the receipt it belongs to.

### Rationale

settled_question#108: no legal obligation binds this project, but an image with no text alternative is unusable to a screen reader and the fix costs nothing. This attribute carries the alt-text behaviour alone — the requirements set withdrew its own copy, so it lives here and nowhere else. The threshold is the binary pass/fail of inspection: with one screen and one image element, anything below 100% is a defect.

### Measure

| | |
|---|---|
| metric | receipt screens whose photo img element carries non-empty alt text naming its receipt |
| threshold | 100% |
| conditions | every rendered state of the receipt screen showing a photo, verified by inspection at code review |

### Traces to

- settled_question#108 — accessibility note (the sole source; no requirement duplicates it)
- requirement#112 — RCP-14 (the screen this viewer lives on)

## INV-NFR-4 — Single-maintainer plainness

### Requirement

While the project is maintained by one person on a 2–4 day appetite, the receipts service shall implement photo storage using only the database and dependencies the repository already runs, apart from python-multipart.

### Rationale

From settled_question#84: one maintainer, a learning project — a plainer solution that keeps working beats a faster one needing an unfamiliar dependency. From settled_question#85: the appetite rules out new infrastructure. The one dependency addition (python-multipart) was settled as a feature cost by requirement#112; backend/requirements.txt read in this run confirms it is absent from the tracked requirements, so the threshold is a real, checkable constraint.

### Measure

| | |
|---|---|
| metric | count of new runtime dependencies in backend/requirements.txt attributable to this feature |
| threshold | 1 (python-multipart) |
| conditions | inspected at the pull request diff, and at every later change touching photo storage |

### Traces to

- settled_question#84 — one maintainer, plainest solution
- settled_question#85 — 2–4 day appetite
- solution_concept#87 — chosen approach

## INV-NFR-5 — Compose-stack self-containment

### Requirement

While the application is deployed by docker compose on the maker's laptop, the receipts service shall serve and store receipt photos using only the existing /data volume and the existing single backend container.

### Rationale

From settled_question#84: the whole thing must come up with one `docker compose up`; no object store, no second service, no cloud account — there is no budget for one. SQLite blob storage in a new receipt_photos table adds nothing to the deployment, which is part of why the concept chose it.

### Measure

| | |
|---|---|
| metric | count of services and volumes added to docker-compose.yml by this feature |
| threshold | 0 |
| conditions | inspected at the pull request diff; a working `docker compose up` against an existing database with real receipts rows |

### Traces to

- settled_question#84 — docker-compose constraint
- solution_concept#87 — SQLite blob choice

## Categories not settled

- **Availability.** settled_question#107 explicitly declines a target: the system runs on a laptop under docker compose. Nothing is proposed, because a percentage on a single-machine personal project would be a wish with a number on it.
- **Scalability.** Explicitly excluded — one active user, no traffic. If a second user ever arrives, settled_question#108 already records that retention and deletion become real questions.
- **Usability, observability.** No threshold named anywhere in this run; nothing proposed.
- **Compliance.** Answered "none" in settled_question#108; the record shows it was asked. The two compliance-like behaviours (confidentiality, cascade retention) are carried by INV-NFR-2 and requirement RCP-9 respectively.
