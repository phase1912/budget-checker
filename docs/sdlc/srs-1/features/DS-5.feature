Feature: Theme toggle switches active theme

  Scenario Outline: Activating the toggle switches from one theme to the other
    Given the application is showing the <current> theme
    When the visitor activates the theme toggle
    Then the application shows the <next> theme

    Examples:
      | current | next  |
      | light   | dark  |
      | dark    | light |
