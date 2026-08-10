Feature: Database unavailability is logged server-side

  Scenario: A database-unavailable failure is recorded server-side
    Given the database is unavailable
    When Sam sends an API request that requires the database
    Then the backend records the failure in its server-side logs

  Scenario: Multiple failures from the same outage are each logged individually
    Given the database is unavailable
    When two separate requests fail because of it
    Then the backend records two separate failures in its server-side logs
