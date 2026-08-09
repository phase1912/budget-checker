Feature: Public landing page access

  Scenario: An anonymous visitor sees the landing page
    Given Alex has no account and no active session
    When Alex opens the landing page
    Then Alex sees the product description

  Scenario: The landing page is never gated behind a login
    Given Alex has no account and no active session
    When Alex opens the landing page
    Then Alex is not redirected to a sign-in screen
    And Alex is not asked for credentials
