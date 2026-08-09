Feature: Shared header and footer across routes

  Scenario: The current route renders inside the shared Layout
    Given a visitor loads the root route
    When the page renders
    Then the shared header is visible
    And the shared footer is visible
    And the route's own content renders between them

  Scenario: Every route is nested under the Layout
    Given the router configuration
    When it is inspected
    Then every route is registered as a child of the Layout root route
