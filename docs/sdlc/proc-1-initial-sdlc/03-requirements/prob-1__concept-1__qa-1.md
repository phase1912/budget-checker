## Requirement

While the backend service is warm (not in a cold-start state), the backend service shall respond to a health-check request within the stated threshold.

## Rationale

The `thresholds` answer explicitly said no concrete numbers exist yet for this pre-launch project, beyond this NFR. This threshold was originally proposed by the maker in proc-1 (no number was given directly by the founder) and confirmed by the founder there, reconfirmed unchanged in this third run's `thresholds` answer.

## Measure

| | |
|---|---|
| metric | response time for the health-check endpoint (e.g. `GET /health`) |
| threshold | 300 ms |
| conditions | single request, backend instance already warm (not resuming from free-tier idle sleep) |

## Traces to

- [[prob-1/concept-1]]

## Metadata

```json
{
  "id": "PERF-NFR-1",
  "title": "Backend warm response time",
  "category": "performance",
  "statement": "While the backend service is warm (not in a cold-start state), the backend service shall respond to a health-check request within 300 ms.",
  "measure": {
    "metric": "response time for GET /health",
    "threshold": "300 ms",
    "conditions": "single request, instance already warm, free-tier hosting",
    "method": "test"
  },
  "rationale": "Proposed by the maker in proc-1, confirmed by the founder there and reconfirmed unchanged in this run.",
  "priority": "should",
  "traces_to": ["prob-1/concept-1"]
}
```
