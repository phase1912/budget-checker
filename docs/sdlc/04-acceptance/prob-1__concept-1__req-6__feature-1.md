## Feature

Apply stored theme preference on load

## Narrative

As a returning visitor
I want the site to load in the theme I chose last time
So that I don't have to re-select it every visit

## Scenarios

```gherkin
Feature: Apply stored theme preference on load

  Scenario: A stored preference is applied on load
    Given the dark theme is stored as the visitor's preference
    When the application loads
    Then the dark theme is the active theme
```

## Traceability

Verifies [[prob-1/concept-1/req-6]].
