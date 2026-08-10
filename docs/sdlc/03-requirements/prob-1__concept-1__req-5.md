## Requirement

If the backend receives invalid input on an API request, then the backend service shall respond with a generic error message.

## Rationale

Traces to the requirements-stage `failure-behaviour` answer: on invalid input, the founder wants an understandable error shown to the caller, with no internal implementation details leaked. Split from logging (see [[prob-1/concept-1/req-8]]) so each half is independently verifiable.

## Verification

test

## Traces to

- [[prob-1/concept-1]]

## Metadata

```json
{
  "id": "ERR-1",
  "title": "Invalid input produces a generic error response",
  "pattern": "unwanted-behaviour",
  "statement": "If the backend receives invalid input on an API request, then the backend service shall respond with a generic error message.",
  "rationale": "failure-behaviour answer: understandable error to the caller, no internal details leaked.",
  "priority": "should",
  "verification": "test",
  "traces_to": ["prob-1/concept-1"]
}
```
