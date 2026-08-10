## Feature

UI icons rendered as vector graphics

## Narrative

As a visitor
I want icon-bearing controls to show clear, legible icons
So that I can recognize what each control does at a glance

## Scenarios

```gherkin
Feature: UI icons rendered as vector graphics

  Scenario: The theme toggle renders a legible vector icon
    Given the header renders
    When the theme toggle control displays
    Then it shows a vector icon rather than plain text or a placeholder

  Scenario: Different icons are visually distinguishable from each other
    Given two different icon-bearing controls render
    When both are visible
    Then each icon's graphic is visually distinct from the other
```

## Traceability

Verifies [[prob-1/concept-1/req-9]].
