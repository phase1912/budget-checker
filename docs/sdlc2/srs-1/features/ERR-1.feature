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
