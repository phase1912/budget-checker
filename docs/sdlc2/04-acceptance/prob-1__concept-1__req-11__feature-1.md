## Feature

Theme toggle persists choice

## Narrative

As a returning visitor
I want my theme choice to be remembered
So that I don't have to re-select it every visit

## Scenarios

```gherkin
Feature: Theme toggle persists choice

  Scenario: Activating the toggle persists the new theme
    Given the application is showing the light theme
    When the visitor activates the theme toggle
    Then the dark theme is stored as the persisted preference

  Scenario: Repeated toggling always reflects the latest choice
    Given the visitor has toggled the theme once already
    When the visitor activates the theme toggle again
    Then the persisted preference is updated to match the newly active theme

  Scenario: The toggle still switches the theme even if persistence fails
    Given localStorage is unavailable in the visitor's browser
    When the visitor activates the theme toggle
    Then the visually active theme still switches for the current session
```

## Traceability

Verifies [[prob-1/concept-1/req-11]].
