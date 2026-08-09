## Requirement

The application shall render every UI icon, including the theme toggle icon, as a vector graphic that visually distinguishes each icon's meaning.

## Rationale

The toggle control (DS-4) and other UI elements need a recognizable icon rather than plain text. This requirement states the outcome the founder needs; [[prob-1/concept-1]]'s "Chosen approach" and "Why not the alternatives" record that the mechanism is the lucide-react library, which is a technology decision rather than something the requirement itself should hard-code.

## Verification

Inspection: render each icon-bearing control and visually confirm it presents a distinct, legible vector icon rather than a placeholder or missing-asset indicator.

## Traces to

- [[prob-1/concept-1]] — "Chosen approach", icons paragraph

## Metadata

```json
{
  "id": "DS-9",
  "title": "UI icons rendered as vector graphics",
  "pattern": "ubiquitous",
  "statement": "The application shall render every UI icon, including the theme toggle icon, as a vector graphic that visually distinguishes each icon's meaning.",
  "rationale": "The toggle control and other UI elements need a recognizable icon rather than plain text; the concept records lucide-react as the chosen mechanism.",
  "priority": "must",
  "verification": "inspection",
  "traces_to": ["prob-1/concept-1"]
}
```
