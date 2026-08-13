# Implementation Note: Container Width Expansion

## Summary
Increased the main page layout container maximum width from `max-w-4xl` (56rem / 896px) to `max-w-6xl` (72rem / 1152px) across Header, Landing page, and Footer components in the budget-checker application frontend.

## Requirements implemented
- Expanded content area container on desktop screens without changing layout responsiveness logic.
- Preserved clean visual alignment between top navigation header bar, central landing content section, and bottom footer component.
- Maintained existing padding (`px-6`) to prevent touch targets or text from hitting screen edges on smaller viewports.

## Symbols changed
- `Function:frontend/src/components/Header.tsx:Header` ([Header.tsx](file:///Users/bohdanrazhyk/Documents/Education/GoIt/budget-checker/frontend/src/components/Header.tsx#L13))
- `Function:frontend/src/components/Footer.tsx:Footer` ([Footer.tsx](file:///Users/bohdanrazhyk/Documents/Education/GoIt/budget-checker/frontend/src/components/Footer.tsx#L4))
- `Function:frontend/src/pages/Landing.tsx:Landing` ([Landing.tsx](file:///Users/bohdanrazhyk/Documents/Education/GoIt/budget-checker/frontend/src/pages/Landing.tsx#L9))

## Design notes
- Utility class `max-w-6xl` (72rem / 1152px) was chosen over `max-w-4xl` (56rem / 896px) to provide a broader reading canvas on desktop monitors while keeping existing padding (`px-6`).
- This change ensures that desktop users utilize screen width effectively while avoiding oversized side margins.
- No changes to colors, theme tokens, or responsive breakpoints were required.

## Risks
- Low risk overall. Layout components are isolated shell wrappers.
- Verified that all 17 unit tests passed cleanly across 7 test files and production bundle (`npm run build`) compiled without warnings or errors.
