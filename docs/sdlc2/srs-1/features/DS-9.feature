Feature: UI icons rendered as vector graphics

  Scenario: The theme toggle renders a legible vector icon
    Given the header renders
    When the theme toggle control displays
    Then it shows a vector icon rather than plain text or a placeholder

  Scenario: Different icons are visually distinguishable from each other
    Given two different icon-bearing controls render
    When both are visible
    Then each icon's graphic is visually distinct from the other
