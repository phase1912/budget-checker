## Requirement

The frontend shall define every color value used in the UI within a single, centrally maintained theme configuration.

## Rationale

Directly serves the founder's success metric in [[prob-1]]: "all colors live in one place" — no component may define its own hex/rgb value. This requirement states the outcome the founder needs; [[prob-1/concept-1]]'s "Chosen approach" records that the mechanism is a Tailwind v4 `@theme` configuration, which is a design/technology decision rather than something the requirement itself should hard-code.

## Verification

Inspection: grep the frontend source for raw hex/rgb color literals outside the theme configuration file; the search must return no matches.

## Traces to

- [[prob-1/concept-1]] — "Chosen approach", tokens paragraph

## Metadata

```json
{
  "id": "DS-1",
  "title": "Single source of truth for color tokens",
  "pattern": "ubiquitous",
  "statement": "The frontend shall define every color value used in the UI within a single, centrally maintained theme configuration.",
  "rationale": "Founder's success metric in the problem brief: all colors live in one place, referenced everywhere, none scattered across components.",
  "priority": "must",
  "verification": "inspection",
  "traces_to": ["prob-1/concept-1"]
}
```
