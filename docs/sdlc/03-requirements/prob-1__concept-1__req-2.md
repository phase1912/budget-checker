## Requirement

When the frontend requests the backend's health-check endpoint, the backend service shall respond indicating it is available.

## Rationale

Demonstrates the architectural skeleton is functional end-to-end — the frontend and backend are deployed as separate services (per the concept's chosen approach) and can actually talk to each other. The `must-have` answer named "skeleton (backend and frontend stood up, talking to each other)" as required for day one.

## Verification

test

## Traces to

- [[prob-1/concept-1]] — Chosen approach (decoupled backend/frontend architecture)

## Metadata

```json
{
  "id": "SKEL-1",
  "title": "Backend reachable from frontend",
  "pattern": "event-driven",
  "statement": "When the frontend requests the backend's health-check endpoint, the backend service shall respond indicating it is available.",
  "rationale": "must-have answer named skeleton connectivity between backend and frontend as required for day one.",
  "priority": "must",
  "verification": "test",
  "traces_to": ["prob-1/concept-1"]
}
```
