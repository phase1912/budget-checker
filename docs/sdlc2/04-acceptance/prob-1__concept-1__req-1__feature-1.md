## Feature

Centralized color tokens

## Narrative

As the person maintaining this frontend
I want every color to come from one theme configuration
So that changing a color is a single edit and no component invents its own value

## Scenarios

```gherkin
Feature: Centralized color tokens

  Scenario: A component uses a color from the theme configuration
    Given the theme configuration defines a color token
    When a component needs that color
    Then the component references the token
    And the rendered UI shows the token's color

  Scenario: A reused color stays consistent across components
    Given two different components both use the same color token
    When both components render
    Then both display the exact same color value

  Scenario: No component defines its own raw color value
    Given the full frontend source
    When it is searched for hex or rgb color literals outside the theme configuration
    Then no such literal is found
```

## Traceability

Verifies [[prob-1/concept-1/req-1]].
