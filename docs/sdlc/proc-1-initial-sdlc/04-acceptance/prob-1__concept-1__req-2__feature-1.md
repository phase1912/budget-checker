## Feature

Backend reachable from frontend

## Narrative

As the person building Budget Checker
I want the frontend to be able to confirm the backend is up
So that I know the skeleton architecture actually connects before building real features on top of it

## Scenarios

```gherkin
Feature: Backend reachable from frontend

  Scenario: The frontend confirms the backend is available
    Given the backend service is running and reachable
    When the frontend requests the backend's health-check endpoint
    Then the backend responds indicating it is available
```

## Traceability

Verifies [[prob-1/concept-1/req-2]].
