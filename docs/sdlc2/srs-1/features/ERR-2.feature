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
