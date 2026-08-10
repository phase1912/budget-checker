## Feature

Draft DB schema defines core entities

## Narrative

As the person building Budget Checker
I want the draft schema to define users, receipts, and budgets as distinct entities
So that later features have a data model to build on instead of starting from nothing

## Scenarios

```gherkin
Feature: Draft DB schema defines core entities

  Scenario: The schema defines all three required entities
    Given the database schema definition
    When it is inspected
    Then it defines an entity for users
    And it defines an entity for receipts
    And it defines an entity for budgets

  Scenario: A schema missing one of the required entities fails inspection
    Given a database schema definition that is missing the receipts entity
    When it is inspected against this requirement
    Then the inspection fails
```

## Traceability

Verifies [[prob-1/concept-1/req-3]].
