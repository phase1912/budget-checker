Feature: Timeout is logged server-side

  Scenario: A timed-out request is logged
    Given a request to the backend is in progress
    When the request exceeds the configured timeout
    Then the backend records the timeout as a failure in its server-side logs

  Scenario: A request finishing exactly at the timeout is not logged as a failure
    Given a request to the backend is in progress
    When the request completes at exactly the configured timeout value
    Then the backend does not record a timeout failure for that request

  Scenario: Multiple timeouts are each logged individually
    Given two separate requests to the backend are in progress
    When both requests exceed the configured timeout
    Then the backend records two separate timeout failures in its server-side logs
