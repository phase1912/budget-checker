## Feature

Receipt create, read, update, delete

## Narrative

As the signed-in owner of my receipts
I want to create a receipt, read one back, amend it and delete it through the API
So that the receipts the tracker shows me are ones I actually put there

## Scenarios

```gherkin
Feature: Receipt create, read, update, delete

  Background:
    Given Sam is signed in to the API

  Scenario: A receipt is created [RCR-1]
    When Sam submits a new receipt with amount 12.50 and description "lunch"
    Then the receipt is created with the submitted amount and description
    And the receipt is owned by Sam
    And the receipt carries a unique identifier and a creation time Sam did not supply

  Scenario: A receipt can be created without a description [RCR-1]
    When Sam submits a new receipt with amount 12.50 and no description
    Then the receipt is created with the submitted amount and no description

  Scenario: A created receipt appears at the top of Sam's list [RCR-1]
    Given Sam already has receipts from earlier
    When Sam submits a new receipt
    Then the new receipt is the first entry in Sam's receipt list

  Scenario: A receipt is read back by identifier [RCR-2]
    Given Sam has a receipt for 12.50 described as "lunch"
    When Sam reads that receipt by its identifier
    Then Sam sees its identifier, amount, description and creation time

  Scenario: An amount is corrected without disturbing anything else [RCR-3]
    Given Sam has a receipt for 12.50 described as "lunch"
    When Sam submits 13.25 as the receipt's amount
    Then the receipt's amount is 13.25
    And the receipt's description is still "lunch"
    And the receipt's identifier and creation time are unchanged

  Scenario: A field not submitted is left alone [RCR-3]
    Given Sam has a receipt for 12.50 described as "lunch"
    When Sam submits only a new description "dinner"
    Then the receipt's description is "dinner"
    And the receipt's amount is still 12.50

  Scenario: A receipt is deleted [RCR-4]
    Given Sam has a receipt
    When Sam deletes that receipt
    Then Sam is told the receipt was deleted
    And reading that receipt by its identifier says it is not found

  Scenario: Deleting a receipt takes its photo with it [RCR-5]
    Given Sam has a receipt with a photo attached
    When Sam deletes that receipt
    Then the receipt's photo is no longer retrievable

  Scenario Outline: A foreign or missing receipt is the same not-found [RCR-6]
    Given Sam has a receipt
    But the receipt named is <a receipt that does not exist|another account's receipt|a receipt that was already deleted>
    When Sam <operation> that receipt by identifier
    Then Sam is told the receipt is not found

    Examples:
      | operation |
      | reads      |
      | updates    |
      | deletes    |

  Scenario Outline: A bad amount is refused and changes nothing [RCR-7]
    When Sam submits a receipt with an amount of <amount>
    Then Sam is told the amount is <why>
    And no receipt exists with that amount

    Examples:
      | amount  | why                        |
      | -5.00   | negative                   |
      | 12.505  | more precise than two decimals |

  Scenario Outline: A bad amount is refused on update too [RCR-7]
    Given Sam has a receipt for 12.50
    When Sam submits an amount of <amount> for that receipt
    Then Sam is told the amount is <why>
    And the receipt's amount is still 12.50

    Examples:
      | amount  | why                        |
      | -5.00   | negative                   |
      | 12.505  | more precise than two decimals |

  Scenario: The list endpoint answers as it always has [RCR-8]
    Given Sam has a receipt with a photo and one without, created before it
    When Sam asks for Sam's receipt list
    Then each entry carries an identifier, amount as a number, description, creation time and a photo flag
    And the entries are newest first
```

## Traceability

RCR-1, RCR-2, RCR-3, RCR-4, RCR-5, RCR-6, RCR-7, RCR-8 — requirement#115, docs/sdlc/receipt-crud-2/05-requirements/.