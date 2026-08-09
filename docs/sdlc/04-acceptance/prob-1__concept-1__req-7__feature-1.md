## Feature

Timeout produces a generic error response

## Narrative

As a caller of the Budget Checker API
I want a clear, generic error when my request takes too long
So that I am not left waiting indefinitely with no feedback

## Scenarios

```gherkin
Feature: Timeout produces a generic error response

  Scenario: A request exceeding the timeout receives a generic error
    Given Sam sends a request to the backend
    When the request exceeds the configured timeout
    Then the backend responds with a generic error message

  Scenario: A request finishing exactly at the timeout is not treated as a failure
    Given Sam sends a request to the backend
    When the request completes at exactly the configured timeout value
    Then the backend does not respond with a timeout error
```

## Traceability

Verifies [[prob-1/concept-1/req-7]].
