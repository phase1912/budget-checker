# Acceptance scenarios — Receipt photos on expenses

The scenarios below cover the requirement set requirement#112 (RCP-1 … RCP-16), drawn from the settled analysis answers (settled_question#129–#132): the happy path, the boundaries that genuinely behave differently, and the mandatory If-then failure cases.

## Feature

Receipt photos on expenses

## Narrative

As someone who records expenses in the budget tracker
I want to attach a photograph of the receipt to the expense
So that I can open the evidence again from the expense itself, without searching my camera roll

## Scenarios

```gherkin
Feature: Receipt photos on expenses

  Background:
    Given Dee is signed in
    And Dee has recorded a receipt for £12.50 with the description "team lunch"

  Scenario: Attaching a photo to a receipt that has none (RCP-1)
    Given the receipt has no photo
    When Dee attaches a jpeg photo of the receipt to it
    Then the photo is stored against that receipt

  Scenario: Opening the photo again in a later session (RCP-2, RCP-14, RCP-16)
    Given the receipt carries a photo Dee attached last week
    When Dee signs in again and opens that receipt's entry
    Then Dee sees the same photo from the receipt's own entry
    And Dee does not leave the app to see it

  Scenario: The receipts screen lists the signed-in person's receipts (RCP-8)
    When Dee opens the receipts screen
    Then Dee sees only Dee's own receipts listed

  Scenario Outline: A photo of exactly the size limit is the boundary (RCP-4)
    Given the receipt has no photo
    When Dee attaches a jpeg photo of <size> to the receipt
    Then the upload is <outcome>

    Examples:
      | size                | outcome  |
      | exactly 5 MB        | accepted |
      | 5 MB and 1 byte     | refused  |

  Scenario: An oversized photo is refused with a message naming both sizes, storing nothing (RCP-4)
    Given the receipt has no photo
    When Dee attaches a jpeg photo of 6 MB to the receipt
    Then Dee is told the limit is 5 MB and the file was 6 MB
    And no photo is stored against the receipt

  Scenario: Non-image bytes are refused even when declared as jpeg (RCP-5)
    Given the receipt has no photo
    When Dee attaches a text file declared as a jpeg
    Then the upload is refused before anything is stored

  Scenario: A second photo to a receipt that already has one is refused as a conflict (RCP-15)
    Given the receipt already carries a photo
    When Dee attaches a second photo to it
    Then Dee is told the receipt already has its one photo
    And the photo already stored is unchanged

  Scenario Outline: Only the owner can read a photo, and every refusal looks the same (RCP-3, RCP-12)
    Given the receipt carries a photo
    When <who> tries to open that receipt's photo
    Then they receive the same not-found answer given for a receipt id that does not exist

    Examples:
      | who                                        |
      | nobody, without signing in                 |
      | another signed-in person, Pat              |
      | a signed-in administrator                  |
      | Dee, but for a receipt that has no photo   |
      | anyone, for a receipt id that does not exist |

  Scenario: Deleting a receipt takes its photo with it (RCP-9)
    Given the receipt carries a photo
    When the receipt is deleted
    Then no photo remains without its receipt

  Scenario: Deleting a user takes every photo with it (RCP-9)
    Given Dee has receipts carrying photos
    When Dee's account is deleted
    Then no photo of Dee's remains without its receipt

  Scenario: An upload aborted part way stores nothing (RCP-10)
    Given the receipt has no photo
    When Dee's photo upload is cut off part way through
    Then no photo is stored against the receipt
    And the receipt itself is unchanged

  Scenario: A database failure during upload leaves nothing behind (RCP-11)
    Given the receipt has no photo
    When the photo upload's database write fails
    Then no photo is stored against the receipt
    And the receipt itself is unchanged

  Scenario: The photo table is created on an existing database without touching receipts (RCP-6, RCP-7)
    Given the database already holds receipts recorded before the photo feature
    When the backend starts
    Then the photo storage table exists
    And the receipts table is exactly as it was before
    And the pre-existing receipts are still readable
```

## Traceability

Verifies [[requirement#112]] — RCP-1, RCP-2, RCP-3, RCP-4, RCP-5, RCP-6, RCP-7, RCP-8, RCP-9, RCP-10, RCP-11, RCP-12, RCP-15 and RCP-16 as scenarios; RCP-13 and RCP-14 through the attach and reopen scenarios against the receipts screen (RCP-8). Size values in the RCP-4 outline are written parameterised in spirit of the settled answer (settled_question#132): the limit number is the one still open, with its fallback decided, so the boundary is "exactly the limit" versus "one past it", not a hard-coded 5 MB.

Deliberately not covered, per settled_question#132: replacing or deleting an attached photo, multiple photos per receipt, thumbnails, and receipt creation/editing — each belongs to no requirement in this set.