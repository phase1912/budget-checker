## Requirement

If the backend receives invalid input on an API request, then the backend service shall record the failure in its server-side logs.

## Rationale

Traces to the requirements-stage `failure-behaviour` answer. Split from the user-facing error response (see [[prob-1/concept-1/req-5]]) so each half is independently verifiable.

## Verification

test

## Traces to

- [[prob-1/concept-1]]

## Metadata

```json
{
  "id": "ERR-4",
  "title": "Invalid input is logged server-side",
  "pattern": "unwanted-behaviour",
  "statement": "If the backend receives invalid input on an API request, then the backend service shall record the failure in its server-side logs.",
  "rationale": "failure-behaviour answer: errors must be logged server-side.",
  "priority": "should",
  "verification": "test",
  "traces_to": ["prob-1/concept-1"]
}
```
