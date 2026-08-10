## Feature

Theme toggle switches active theme

## Narrative

As a visitor
I want the toggle to switch between light and dark
So that I can view the site in whichever theme I prefer right now

## Scenarios

```gherkin
Feature: Theme toggle switches active theme

  Scenario Outline: Activating the toggle switches from one theme to the other
    Given the application is showing the <current> theme
    When the visitor activates the theme toggle
    Then the application shows the <next> theme

    Examples:
      | current | next  |
      | light   | dark  |
      | dark    | light |
```

## Traceability

Verifies [[prob-1/concept-1/req-5]].
