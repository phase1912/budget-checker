## Feature

Invalid input produces a generic error response

## Narrative

As a caller of the Budget Checker API
I want a clear, generic error when my request is invalid
So that I know something was wrong without seeing internal implementation details

## Scenarios

```gherkin
Feature: Invalid input produces a generic error response

  Scenario Outline: Invalid input is rejected with a generic error
    Given Sam sends an API request with <problem>
    When the backend processes the request
    Then the backend responds with a generic error message
    And the response does not expose internal implementation details

    Examples:
      | problem                       |
      | a missing required field      |
      | a field of the wrong type     |
      | a malformed request body      |
```

## Traceability

Verifies [[prob-1/concept-1/req-5]].
