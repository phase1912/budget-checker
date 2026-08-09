Feature: Invalid input is logged server-side

  Scenario: Invalid input is recorded server-side
    Given Sam sends an API request with a missing required field
    When the backend processes the request
    Then the backend records the failure in its server-side logs

  Scenario: Multiple invalid requests are each logged individually
    Given Sam sends two separate API requests, each with invalid input
    When the backend processes both requests
    Then the backend records two separate failures in its server-side logs
