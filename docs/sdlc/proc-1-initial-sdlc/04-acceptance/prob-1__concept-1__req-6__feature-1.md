## Feature

Database unavailability produces a generic error response

## Narrative

As a caller of the Budget Checker API
I want a clear, generic error when the database can't be reached
So that I see a sensible failure instead of a hang or a leaked internal error

## Scenarios

```gherkin
Feature: Database unavailability produces a generic error response

  Scenario: A request fails gracefully when the database is unavailable
    Given the database is unavailable
    When Sam sends an API request that requires the database
    Then the backend responds with a generic error message
    And the response does not expose internal implementation details

  Scenario: The database becoming unavailable mid-request still fails gracefully
    Given the database becomes unavailable while Sam's request is being processed
    When the backend cannot complete the request
    Then the backend responds with a generic error message
```

## Traceability

Verifies [[prob-1/concept-1/req-6]].
