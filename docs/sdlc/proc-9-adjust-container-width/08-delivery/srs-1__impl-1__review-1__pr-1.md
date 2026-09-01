https://github.com/phase1912/budget-checker/pull/5

# Pull Request: Multi-Device Responsive Container Layout Adaptation

## Summary
Widens the shared page container and makes it responsive across the app's Header, Footer, and Landing page, replacing a flat max-width with breakpoint-scaled sizing so tablets and desktops get intermediate steps instead of jumping straight from a mobile width to the largest desktop width. During review ([[srs-1/impl-1/review-1]]), the initially-committed implementation was found to ship a flat `w-full max-w-7xl` container — the design the concept brief ([[prob-1/concept-1]]) explicitly evaluated and rejected in favor of staged breakpoint scaling. This PR carries the corrected implementation that matches the approved requirement.

## Requirements covered
- [[prob-1/concept-1/req-1]]: Container now applies `w-full px-4 sm:px-6 sm:max-w-2xl md:max-w-4xl lg:max-w-6xl xl:max-w-7xl` across Header, Footer, and Landing.
- [[prob-1/concept-1/qa-1]]: Verified 0px horizontal page overflow at 375px (mobile), 768px (tablet), and 1280px (desktop) viewports.

## Testing
- `npm test --prefix frontend -- --run`: 17/17 tests passed across 7 test files, including the updated `Layout.test.tsx` assertion checking for the staged breakpoint classes (`sm:max-w-2xl`, `md:max-w-4xl`, `lg:max-w-6xl`, `xl:max-w-7xl`).
- `npm run build --prefix frontend`: `tsc --noEmit && vite build` completed cleanly with no type or bundling errors.
- Manually verified in-browser at 375px, 768px, and 1280px viewports: computed container `max-width` steps from `none` (mobile) → `896px` (`md`, tablet) → `1280px` (`xl`, desktop) as expected, with zero horizontal scroll at every tier.
- See [[srs-1/impl-1/verify-1]] for the original verification baseline (same commands, prior implementation, before this correction).

## Risk and blast radius
- Pure Tailwind `className` changes in three presentational components (`Header`, `Footer`, `Landing`) — no logic, props, or MobX store changes.
- `impact(direction: "upstream")` on all three symbols returns LOW risk, 1–3 direct dependents each (`Layout.tsx`, `App.tsx`, and their tests) — structural JSX composition only; none of those dependents branch on the container's class string.
- `detect_changes({scope: "compare", base_ref: "master"})` reports `risk_level: "high"`, but per [[srs-1/impl-1/review-1]] this is driven by `Header`'s structural centrality across 6 cross-community `App` process traces (theme, auth modal, storage) — none of those flows read or branch on the container's classes, so the functional blast radius is LOW.
- Full analysis and the requirement-conformance finding that led to this correction are recorded in [[srs-1/impl-1/review-1]].
