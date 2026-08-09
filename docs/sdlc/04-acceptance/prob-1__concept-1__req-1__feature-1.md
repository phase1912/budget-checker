## Feature

Public landing page access

## Narrative

As an anonymous visitor
I want to see the product description without signing up
So that I can decide whether Budget Checker is worth trying before committing to an account

## Scenarios

```gherkin
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
```

## Traceability

Verifies [[prob-1/concept-1/req-1]].
