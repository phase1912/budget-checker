## Feature

Budgets and spend summary

## Narrative

As a signed-in budget-checker user tracking their own spending
I want to set a target for a period and read a summary of that period
So that I can see spent, remaining and whether I am over it without doing the arithmetic myself

## Scenarios

```gherkin
Feature: Budgets and spend summary

  Background:
    Given Alex is signed in
    And the period is "2025-03"

  Scenario: A budget is set for a period (BUD-1, BUD-11)
    When Alex sets a target of "150.00" for the period
    Then the summary for the period shows a target of 150.00

  Scenario: The summary shows spent, remaining and over for a period under target (BUD-3)
    Given a target of "150.00" is set for the period
    And Alex has receipts totalling 90.00 inside the period's month
    When Alex reads the summary for the period
    Then the summary shows 90.00 spent
    And the summary shows 60.00 remaining
    And the summary shows Alex is not over

  Scenario: The summary shows over when spending exceeds the target (BUD-3)
    Given a target of "150.00" is set for the period
    And Alex has receipts totalling 175.50 inside the period's month
    When Alex reads the summary for the period
    Then the summary shows 175.50 spent
    And the summary shows Alex is over

  Scenario: Setting the same period again replaces the target (BUD-2)
    Given a target of "150.00" is set for the period
    When Alex sets a target of "200.00" for the period again
    Then the summary for the period shows a target of 200.00

  Scenario: Re-setting the target changes the over flag (BUD-2, BUD-3)
    Given a target of "150.00" is set for the period
    And Alex has receipts totalling 175.50 inside the period's month
    When Alex sets a target of "200.00" for the period again
    Then the summary shows Alex is not over

  Scenario Outline: Receipts count only inside the month boundaries (BUD-4)
    Given a target of "150.00" is set for the period
    And Alex has a receipt for 10.00 timestamped <when> UTC
    When Alex reads the summary for the period
    Then the summary shows <spent> spent

    Examples:
      | when                                | spent |
      | 1 March 2025 at midnight            | 10.00 |
      | 15 March 2025 at noon               | 10.00 |
      | 1 April 2025 at midnight            | 0.00  |

  Scenario: A summary for a period with no budget says none is set (BUD-5)
    When Alex reads the summary for a period they never set
    Then Alex is told no budget is set for that period
    And the summary does not report a target of zero

  Scenario Outline: A malformed period is refused with the rule named (BUD-6)
    When Alex sets a target of "150.00" for the period "<period>"
    Then the request is refused
    And the refusal names the required "YYYY-MM" format

    Examples:
      | period   |
      | 2024-13  |
      | 24-01    |

  Scenario Outline: An invalid target is refused with the rule named (BUD-7)
    When Alex sets a target of "<amount>" for the period
    Then the request is refused
    And the refusal names the accepted target rule

    Examples:
      | amount  |
      | -10.00  |
      | 0.00    |
      | 10.999  |

  Scenario: Another user's budget is answered the same as no budget (BUD-8)
    Given a target of "150.00" is set for the period by Priya
    When Alex reads the summary for the period
    Then Alex is told no budget is set for that period
    And the response carries none of Priya's target

  Scenario: A request with no valid authenticated user is refused like receipts (BUD-9)
    Given a request is made without a valid authenticated user
    When the budgets summary for the period is read
    Then the request is refused the same way an unauthenticated receipts request is

  Scenario: Duplicate budget rows are read deterministically and indicated (BUD-10)
    Given two budget rows exist in storage for Alex and the period
    When Alex reads the summary for the period twice
    Then both reads show the same target of 150.00
    And the response indicates the duplication
```

## Traceability

Verifies [[req#114/BUD-1]] through [[req#114/BUD-11]]: the happy path (BUD-1, BUD-3, BUD-11), the boundaries settled as genuinely different (BUD-2 re-set, BUD-4 inclusive-exclusive month boundaries via Scenario Outline, BUD-5 empty period, BUD-7 just-past-maximum target via Scenario Outline), and the mandatory failure cases for every If…then requirement (BUD-5, BUD-6, BUD-7, BUD-8, BUD-9, BUD-10). One scenario per requirement; no scenario covers what the requirement set does not say (timezone normalisation, concurrency, latency — none are settled).