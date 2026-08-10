## Requirement

If localStorage is unavailable or contains no stored theme preference, then the application shall apply the operating system's prefers-color-scheme setting.

## Rationale

Founder's answer to the failure-behaviour question: a graceful fallback is required so the application never breaks or looks wrong when there is no stored choice (e.g. first visit, or private browsing where localStorage may be restricted).

## Verification

Test: with localStorage cleared/unavailable and the OS/browser set to a specific color-scheme preference, load the application and assert the applied theme matches that OS preference.

## Traces to

- [[prob-1/concept-1]] — "Chosen approach", dark mode paragraph

## Metadata

```json
{
  "id": "DS-7",
  "title": "Fallback to OS theme preference",
  "pattern": "unwanted-behaviour",
  "statement": "If localStorage is unavailable or contains no stored theme preference, then the application shall apply the operating system's prefers-color-scheme setting.",
  "rationale": "Founder: graceful fallback to light theme required when localStorage/stored preference is unavailable, first checking the OS-level preference.",
  "priority": "must",
  "verification": "test",
  "traces_to": ["prob-1/concept-1"]
}
```
