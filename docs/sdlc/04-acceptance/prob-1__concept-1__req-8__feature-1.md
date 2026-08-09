## Feature

Default to light theme

## Narrative

As a first-time visitor whose system has no color-scheme preference set
I want the site to still load in a sensible, defined theme
So that nothing looks broken or undefined

## Scenarios

```gherkin
Feature: Default to light theme

  Scenario: No stored preference and no OS preference, so light is applied
    Given no theme preference is stored
    And the operating system reports no color-scheme preference
    When the application loads
    Then the light theme is applied
```

## Traceability

Verifies [[prob-1/concept-1/req-8]].
