## Requirement

While the color token palette is used to render text against a background, the frontend shall maintain a contrast ratio that meets WCAG 2.1 AA.

## Rationale

Founder's answer to `thresholds`/`compliance`: no formal legal accessibility requirement applies, but the founder wants a baseline WCAG AA contrast bar built into the palette now, since it is cheap to enforce while the tokens are first being defined and expensive to retrofit into a palette already in use everywhere.

## Measure

| | |
|---|---|
| metric | contrast ratio between each token's foreground/text color and the background color it is defined to be used against |
| threshold | at least 4.5:1 for normal-size text (WCAG 2.1 AA), at least 3:1 for large-scale text |
| conditions | evaluated for every token pairing intended for text-on-background use, in both the light and dark theme variants |

## Traces to

- [[prob-1/concept-1]]

## Metadata

```json
{
  "id": "DS-NFR-1",
  "title": "WCAG AA contrast for token palette",
  "category": "accessibility",
  "statement": "While the color token palette is used to render text against a background, the frontend shall maintain a contrast ratio that meets WCAG 2.1 AA.",
  "measure": {
    "metric": "contrast ratio between each token's foreground/text color and its intended background color",
    "threshold": "4.5:1 for normal text, 3:1 for large-scale text",
    "conditions": "evaluated for every text-on-background token pairing, in both light and dark theme variants",
    "method": "analysis"
  },
  "rationale": "Founder: no formal compliance requirement exists, but wants baseline WCAG AA contrast built into the palette now since it is cheap now and expensive to retrofit later.",
  "priority": "must",
  "traces_to": ["prob-1/concept-1"]
}
```
