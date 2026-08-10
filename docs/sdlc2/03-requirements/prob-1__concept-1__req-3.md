## Requirement

The router shall mount the Landing page as the content of the Layout at the root path.

## Rationale

Realizes the "router-ready foundation" chosen in [[prob-1/concept-1]]: a router exists now, with Layout as the root layout route, even though there is only one page today — so future pages are added as new routes without restructuring.

## Verification

Test: an automated navigation test requests the root path and asserts the Landing page content renders inside the Layout.

## Traces to

- [[prob-1/concept-1]] — "Chosen approach", Layout paragraph

## Metadata

```json
{
  "id": "DS-3",
  "title": "Router mounts Landing at root path",
  "pattern": "ubiquitous",
  "statement": "The router shall mount the Landing page as the content of the Layout at the root path.",
  "rationale": "Router-ready foundation chosen in the concept: Layout is the root route, Landing is today's only child route.",
  "priority": "must",
  "verification": "test",
  "traces_to": ["prob-1/concept-1"]
}
```
