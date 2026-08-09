## Requirement

If the database is unavailable when the backend processes a request, then the backend service shall record the failure in its server-side logs.

## Rationale

Traces to the requirements-stage `failure-behaviour` answer, applied to the DB-unavailable failure mode. Split from the user-facing error response (see [[prob-1/concept-1/req-6]]) so each half is independently verifiable.

## Verification

test

## Traces to

- [[prob-1/concept-1]]

## Metadata

```json
{
  "id": "ERR-5",
  "title": "Database unavailability is logged server-side",
  "pattern": "unwanted-behaviour",
  "statement": "If the database is unavailable when the backend processes a request, then the backend service shall record the failure in its server-side logs.",
  "rationale": "failure-behaviour answer: errors must be logged server-side.",
  "priority": "should",
  "verification": "test",
  "traces_to": ["prob-1/concept-1"]
}
```
