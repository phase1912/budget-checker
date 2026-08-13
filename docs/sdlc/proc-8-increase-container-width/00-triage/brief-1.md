# Change Brief: Increase Container Width

## What changes
The main layout container max-width will be increased from `max-w-4xl` (896px) to `max-w-6xl` (1152px) across the Header, Landing page, and Footer components in the frontend.

## Kind of change
chore

## Why this kind
Changing the layout container max-width is a straightforward CSS styling tweak that improves the desktop layout appearance without changing any business logic, API contracts, or stored database schemas.

## Expected blast radius
Upstream impact analysis performed with Meridian (`npx meridian impact -r budget-checker Header`) indicates `LOW` risk.
Affected components:
- `frontend/src/components/Header.tsx`
- `frontend/src/components/Footer.tsx`
- `frontend/src/pages/Landing.tsx`
Parent container/layout caller: `frontend/src/components/Layout.tsx` -> `frontend/src/App.tsx`.

## Acceptance criteria
1. Header container class updated to `max-w-6xl`.
2. Landing page main container class updated to `max-w-6xl`.
3. Footer container class updated to `max-w-6xl`.
4. Visual layout renders cleanly without layout overflow or broken styling.
5. All existing frontend tests pass.

## Out of scope
- Responsive media queries or mobile-specific adaptive layout redesign.
- Backend, API, or database changes.

## Open questions
None.
