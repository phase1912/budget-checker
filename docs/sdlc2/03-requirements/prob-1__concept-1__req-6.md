## Requirement

When the application loads, the application shall apply the theme stored in localStorage if a stored preference exists.

## Rationale

Completes the persistence loop for the founder's "persisted across visits" success metric ([[prob-1]]) — persisting a choice is only useful if it is read back on the next visit.

## Verification

Test: set a theme preference in localStorage, load the application, and assert the applied theme matches the stored value.

## Traces to

- [[prob-1/concept-1]] — "Chosen approach", dark mode paragraph

## Metadata

```json
{
  "id": "DS-6",
  "title": "Apply stored theme preference on load",
  "pattern": "event-driven",
  "statement": "When the application loads, the application shall apply the theme stored in localStorage if a stored preference exists.",
  "rationale": "Persisting a theme choice is only useful if it is read back on the next visit.",
  "priority": "must",
  "verification": "test",
  "traces_to": ["prob-1/concept-1"]
}
```
