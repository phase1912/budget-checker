## Feature

Fallback to OS theme preference

## Narrative

As a first-time visitor with no saved preference
I want the site to match my system's light/dark setting
So that it looks right without me having to configure anything

## Scenarios

```gherkin
Feature: Fallback to OS theme preference

  Scenario Outline: No stored preference exists, so the OS preference is applied
    Given no theme preference is stored
    And the operating system reports a <preference> preference
    When the application loads
    Then the <preference> theme is applied

    Examples:
      | preference |
      | light      |
      | dark       |

  Scenario: localStorage is unavailable, so the OS preference is used instead
    Given localStorage is unavailable in the visitor's browser
    And the operating system reports a light-mode preference
    When the application loads
    Then the light theme is applied
```

## Traceability

Verifies [[prob-1/concept-1/req-7]].
