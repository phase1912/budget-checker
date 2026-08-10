## Feature

Landing page redesign

## Narrative

As a visitor to the landing page
I want to see a designed, styled page
So that the product looks trustworthy and finished rather than unstyled markup

## Scenarios

```gherkin
Feature: Landing page redesign

  Scenario: The landing page shows styled content
    Given a visitor opens the landing page
    When the page renders
    Then the heading, body text, and status line are styled with the theme's typography, color, and spacing
    And no element renders with unstyled default browser presentation
```

## Traceability

Verifies [[prob-1/concept-1/req-10]].
