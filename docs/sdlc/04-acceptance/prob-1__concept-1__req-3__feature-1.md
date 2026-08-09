## Feature

Router mounts Landing at root path

## Narrative

As a visitor
I want the landing page to load when I visit the site's root URL
So that I land on the intended page

## Scenarios

```gherkin
Feature: Router mounts Landing at root path

  Scenario: The root path renders the Landing page
    Given a visitor requests the root path "/"
    When the router resolves the request
    Then the Landing page's content renders inside the shared Layout
```

## Traceability

Verifies [[prob-1/concept-1/req-3]].

Note: behaviour for unmatched paths is out of scope for this requirement and is covered by the separate not-found requirement (DS-13, pending formal registration as a fast-follow — see the `unknown-route-behaviour` decision recorded on this branch).
