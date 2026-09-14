## Requirement

While the backend service is resuming from a free-tier idle sleep, the backend service shall become responsive to a health-check request within the stated threshold.

## Rationale

The concept document ([[prob-1/concept-1]], Risks section) cites researched Render free-tier behavior (sleeps after 15 minutes of inactivity, 30–60s cold start). This threshold was originally proposed by the maker in proc-1 from that research and confirmed by the founder there, reconfirmed unchanged in this third run's `thresholds` answer.

## Measure

| | |
|---|---|
| metric | time from first request after idle sleep to a successful health-check response |
| threshold | 60 seconds |
| conditions | after at least 15 minutes of inactivity on the free-tier host (e.g. Render free web service) |

## Traces to

- [[prob-1/concept-1]]

## Metadata

```json
{
  "id": "AVAIL-NFR-1",
  "title": "Backend cold-start recovery time",
  "category": "availability",
  "statement": "While the backend service is resuming from a free-tier idle sleep, the backend service shall become responsive to a health-check request within 60 seconds.",
  "measure": {
    "metric": "time to first successful health-check response after idle sleep",
    "threshold": "60 seconds",
    "conditions": "after at least 15 minutes of inactivity on the free-tier host",
    "method": "test"
  },
  "rationale": "Proposed by the maker in proc-1 from researched Render free-tier cold-start behavior, confirmed by the founder there and reconfirmed unchanged in this run.",
  "priority": "should",
  "traces_to": ["prob-1/concept-1"]
}
```
