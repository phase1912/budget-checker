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
