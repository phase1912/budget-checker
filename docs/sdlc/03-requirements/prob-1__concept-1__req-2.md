## Requirement

The application shall render a shared header and footer around the content of every route through a single Layout component.

## Rationale

Directly implements the founder's SPA clarification recorded in [[prob-1]]'s Assumptions section: header and footer are persistent chrome, not per-page markup, and [[prob-1/concept-1]] chose the router-ready foundation specifically so this holds for every current and future route.

## Verification

Demonstration: navigate the running application and confirm the header and footer remain present and unchanged while only the routed content area changes.

## Traces to

- [[prob-1/concept-1]] — "Chosen approach", Layout paragraph

## Metadata

```json
{
  "id": "DS-2",
  "title": "Shared Layout renders header and footer",
  "pattern": "ubiquitous",
  "statement": "The application shall render a shared header and footer around the content of every route through a single Layout component.",
  "rationale": "Founder's SPA clarification: header/footer are shared chrome, only content changes between views.",
  "priority": "must",
  "verification": "demonstration",
  "traces_to": ["prob-1/concept-1"]
}
```
