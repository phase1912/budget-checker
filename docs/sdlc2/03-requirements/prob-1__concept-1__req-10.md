## Requirement

The Landing page shall present its content styled with the Tailwind theme tokens instead of the current unstyled markup.

## Rationale

Directly serves the founder's success metric in [[prob-1]]: the landing page is visibly redesigned, replacing the bare unstyled JSX confirmed present today (see `existing-behaviour` answer to this stage).

## Verification

Demonstration: render the Landing page and visually confirm it uses the theme's colors, spacing, and typography rather than default browser styling.

## Traces to

- [[prob-1/concept-1]] — "Chosen approach", landing page paragraph

## Metadata

```json
{
  "id": "DS-10",
  "title": "Landing page styled with token palette",
  "pattern": "ubiquitous",
  "statement": "The Landing page shall present its content styled with the Tailwind theme tokens instead of the current unstyled markup.",
  "rationale": "Founder's success metric: the landing page is visibly redesigned with a new design.",
  "priority": "must",
  "verification": "demonstration",
  "traces_to": ["prob-1/concept-1"]
}
```
