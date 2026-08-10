## Requirement

When the user activates the theme toggle, the application shall persist the resulting theme to localStorage.

## Rationale

Serves the founder's success metric that the theme choice is "persisted across visits" ([[prob-1]], Success metrics). Split out from theme-switching (DS-5) because switching and persisting are two independently verifiable capabilities: a build could switch the theme without persisting it, or vice versa, and each needs its own test.

## Verification

Test: activate the toggle and assert the persisted value in localStorage matches the newly active theme.

## Traces to

- [[prob-1/concept-1]] — "Chosen approach", dark mode paragraph

## Metadata

```json
{
  "id": "DS-11",
  "title": "Theme toggle persists choice to localStorage",
  "pattern": "event-driven",
  "statement": "When the user activates the theme toggle, the application shall persist the resulting theme to localStorage.",
  "rationale": "Founder's success metric: theme choice persisted across visits.",
  "priority": "must",
  "verification": "test",
  "traces_to": ["prob-1/concept-1"]
}
```
