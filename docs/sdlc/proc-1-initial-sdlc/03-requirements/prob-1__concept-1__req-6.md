## Requirement

If the database is unavailable when the backend processes a request, then the backend service shall respond with a generic error message.

## Rationale

Traces to the requirements-stage `failure-behaviour` answer, applied to the DB-unavailable failure mode. Split from logging (see [[prob-1/concept-1/req-9]]) so each half is independently verifiable.

## Verification

test

## Traces to

- [[prob-1/concept-1]]

## Metadata

```json
{
  "id": "ERR-2",
  "title": "Database unavailability produces a generic error response",
  "pattern": "unwanted-behaviour",
  "statement": "If the database is unavailable when the backend processes a request, then the backend service shall respond with a generic error message.",
  "rationale": "failure-behaviour answer named a dependency being down as a case to handle at basic level.",
  "priority": "should",
  "verification": "test",
  "traces_to": ["prob-1/concept-1"]
}
```
