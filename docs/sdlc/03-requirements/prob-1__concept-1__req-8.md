## Requirement

If neither a stored theme preference nor an operating system color-scheme preference is available, then the application shall apply the light theme.

## Rationale

Completes the founder's fallback chain from the failure-behaviour answer: localStorage, then OS preference, then light as the final default — the application must always resolve to a defined theme rather than an undefined or broken state.

## Verification

Test: with localStorage cleared/unavailable and no OS color-scheme preference exposed, load the application and assert the light theme is applied.

## Traces to

- [[prob-1/concept-1]] — "Chosen approach", dark mode paragraph

## Metadata

```json
{
  "id": "DS-8",
  "title": "Default to light theme",
  "pattern": "unwanted-behaviour",
  "statement": "If neither a stored theme preference nor an operating system color-scheme preference is available, then the application shall apply the light theme.",
  "rationale": "Founder: graceful fallback to light theme as the final default in the absence of any other signal.",
  "priority": "must",
  "verification": "test",
  "traces_to": ["prob-1/concept-1"]
}
```
