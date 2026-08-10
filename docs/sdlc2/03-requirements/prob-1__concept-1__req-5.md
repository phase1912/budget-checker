## Requirement

When the user activates the theme toggle, the application shall switch the active theme between light and dark.

## Rationale

Directly implements the header control required by DS-4, giving it an observable effect. Serves the founder's success metric of a working theme toggle in [[prob-1]].

## Verification

Test: activate the toggle and assert the rendered theme changes from its current value to the other value.

## Traces to

- [[prob-1/concept-1]] — "Chosen approach", dark mode paragraph

## Metadata

```json
{
  "id": "DS-5",
  "title": "Theme toggle switches the active theme",
  "pattern": "event-driven",
  "statement": "When the user activates the theme toggle, the application shall switch the active theme between light and dark.",
  "rationale": "Founder's success metric: a working light/dark theme toggle in the header.",
  "priority": "must",
  "verification": "test",
  "traces_to": ["prob-1/concept-1"]
}
```
