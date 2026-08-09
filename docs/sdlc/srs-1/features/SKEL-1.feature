Feature: Backend reachable from frontend

  Scenario: The frontend confirms the backend is available
    Given the backend service is running and reachable
    When the frontend requests the backend's health-check endpoint
    Then the backend responds indicating it is available
