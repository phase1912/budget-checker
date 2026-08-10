Feature: DB schema supports deleting a user's data

  Scenario: Deleting a user with receipts and budgets leaves no orphaned records
    Given a user has receipts and budgets recorded against their account
    When the user is deleted
    Then no receipts row referencing that user remains
    And no budgets row referencing that user remains

  Scenario: Deleting a user with no dependent records succeeds cleanly
    Given a user has no receipts and no budgets recorded
    When the user is deleted
    Then the deletion succeeds without error
