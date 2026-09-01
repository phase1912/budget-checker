# Concept Brief: Multi-Device Responsive Container Layout Adaptation

Parent problem brief: [[prob-1]]

## Options considered

### Option 1: Responsive Breakpoints via Tailwind CSS v4 (Chosen)
Utilize Tailwind CSS v4 responsive breakpoint modifier classes (`px-4`, `sm:px-6`, `sm:max-w-2xl`, `md:max-w-4xl`, `lg:max-w-6xl`, `xl:max-w-7xl`) directly on layout section container wrappers in `Header.tsx`, `Landing.tsx`, and `Footer.tsx`.

### Option 2: Fixed Global Full-Width Container (`w-full max-w-7xl`)
Apply a single static `w-full max-w-7xl` container class across all viewports without intermediate tablet (`sm:`, `md:`) breakpoint scaling.

### Option 3: Do Nothing
Retain current layout container configurations, leaving mobile and tablet viewports without fluid scaling.

## Chosen approach
Option 1. Using responsive utility modifiers in Tailwind CSS v4 provides smooth, multi-tier layout scaling across mobile smartphones (<640px), tablets (640px-1024px), and widescreen desktop PC displays (≥1024px) without adding custom CSS overrides or complex runtime dependencies.

## Why not the alternatives
- **Option 2** fails to provide fluid intermediate scaling for tablet viewports and causes aggressive margin shifts on smaller screens.
- **Option 3** leaves the problem unresolved and causes poor readability on mobile devices.

## Constraints
- Must maintain existing component architecture across `Header.tsx`, `Landing.tsx`, and `Footer.tsx`.
- Must rely exclusively on standard Tailwind CSS v4 utility classes without introducing external layout libraries.

## Assumptions
- Modifying wrapper container classes in JSX does not break internal child element positioning or MobX store bindings.
- Viewport breakpoints adhere to standard Tailwind screen width conventions (`sm: 640px`, `md: 768px`, `lg: 1024px`, `xl: 1280px`).

## Risks
- Minor visual alignment variations if custom sub-components carry hardcoded inline widths.
- Mitigation: Verify layout visually across viewport breakpoints and run existing frontend test suite.

## Out of scope
- Mobile navigation drawer or hamburger menu overhaul.
- Backend API contract alterations or MobX state refactoring.
