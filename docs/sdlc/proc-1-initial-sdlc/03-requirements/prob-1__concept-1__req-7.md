## Requirement

If a request to the backend exceeds the configured timeout, then the backend service shall respond with a generic error message.

## Rationale

Traces to the requirements-stage `failure-behaviour` answer, applied to the timeout failure mode. Split from logging (see [[prob-1/concept-1/req-10]]) so each half is independently verifiable.

## Verification

test

## Traces to

- [[prob-1/concept-1]]

## Metadata

```json
{
  "id": "ERR-3",
  "title": "Timeout produces a generic error response",
  "pattern": "unwanted-behaviour",
  "statement": "If a request to the backend exceeds the configured timeout, then the backend service shall respond with a generic error message.",
  "rationale": "failure-behaviour answer named a timeout as a case to handle at basic level.",
  "priority": "should",
  "verification": "test",
  "traces_to": ["prob-1/concept-1"]
}
```
