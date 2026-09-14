## Requirement

The database schema shall support deletion of a user's data without leaving orphaned records in dependent tables.

## Rationale

Traces to the requirements-stage `compliance` answer: a GDPR-adjacent requirement that the schema must allow deleting a user's data. Dependent tables are records that reference a user (e.g. their receipts and budgets) — deleting the user must not leave unreferenced rows behind.

## Verification

analysis

## Traces to

- [[prob-1/concept-1]] — Constraints

## Metadata

```json
{
  "id": "DATA-2",
  "title": "DB schema supports deleting a user's data",
  "pattern": "ubiquitous",
  "statement": "The database schema shall support deletion of a user's data without leaving orphaned records in dependent tables.",
  "rationale": "compliance answer: draft schema must account for the ability to delete user data (right-to-erasure-style design consideration).",
  "priority": "must",
  "verification": "analysis",
  "traces_to": ["prob-1/concept-1"]
}
```
