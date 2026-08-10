https://github.com/phase1912/budget-checker/pull/2

## Summary

Establishes the frontend's design system foundation: a single Tailwind v4 theme configuration as the sole source of color (green primary, indigo accent, semantic error/warning/info, neutral chrome, with distinct light/dark values per token), a router-ready shared `Layout` (react-router-dom v6) providing a consistent header and footer across every route, a full light/dark theme with a header toggle, `localStorage` persistence, and a two-level fallback (stored preference → OS preference → light), vector icons via `lucide-react`, and a redesigned, token-styled landing page. `App.tsx` now defines a route tree instead of rendering the landing page directly.

## Requirements covered

- [[prob-1/concept-1/req-1]] — every color value comes from a single, centrally maintained theme configuration.
- [[prob-1/concept-1/req-2]] — a shared header and footer render around every route through one `Layout` component.
- [[prob-1/concept-1/req-3]] — the router mounts the landing page at the root path within `Layout`.
- [[prob-1/concept-1/req-4]] — the header exposes a theme toggle control.
- [[prob-1/concept-1/req-5]] — activating the toggle switches the active theme.
- [[prob-1/concept-1/req-11]] — activating the toggle persists the new theme to `localStorage`.
- [[prob-1/concept-1/req-6]] — the application applies a stored theme preference on load.
- [[prob-1/concept-1/req-7]] — falls back to the OS `prefers-color-scheme` setting when nothing is stored.
- [[prob-1/concept-1/req-8]] — defaults to light when neither a stored nor an OS preference is available.
- [[prob-1/concept-1/req-9]] — UI icons render as vector graphics that are visually distinguishable.
- [[prob-1/concept-1/req-10]] — the landing page is styled with the token palette instead of unstyled markup.
- [[prob-1/concept-1/qa-1]] — the token palette targets WCAG 2.1 AA contrast (light-theme pairs hand-verified; see [[srs-1/impl-1]]).

Also implemented ahead of formal requirement registration, per an explicit founder decision recorded during the acceptance stage (see [[srs-1/impl-1]] Design notes and [[srs-1]] Open questions): distinct light/dark values for every token, and a dedicated not-found page with a redirect for unmatched routes. Both still need their own EARS requirement and acceptance-scenario artifacts as a follow-up.

## Testing

From [[srs-1/impl-1/verify-1]]: `cd frontend && npm run build` (`tsc --noEmit && vite build`) passes; `cd frontend && npm test` (`vitest run`) passes, 6 test files / 15 tests. 19 of 23 approved acceptance scenarios are covered by an automated test; the remaining 4 are either verification-method inspection/demonstration by design, or same-code-path variants of an already-tested case — all named explicitly in the verification report rather than silently dropped. Manually verified in a browser: light/dark rendering, the theme toggle updating `localStorage` and the `dark` class, the OS-preference fallback firing on first load, and the not-found redirect. No linter/formatter exists in this project (confirmed, not overlooked).

## Risk and blast radius

From [[srs-1/impl-1/review-1]]: blast radius is `App` and `Landing.tsx`, both inside this diff, plus `Landing.test.tsx` (unmodified, still passing — its assertions target content/semantics, not styling). No dependent outside the diff was found unaccounted for; `impact()` confirmed both changed symbols carry LOW risk. Five independent review passes (correctness, security, blast radius, coverage, adversarial) found no defect.

Two non-blocking residual risks, carried forward for awareness: `ThemeStore` (a new module-level singleton, matching the existing `HealthStore` pattern) assumes a DOM exists at import time — not reachable today since this is a pure client-side SPA with no SSR, but worth knowing before that changes. The manual `.dark` class toggle and this feature's semantic CSS tokens must stay in sync by convention — a future change styling something with Tailwind's built-in `dark:` variant instead of these tokens would silently stop respecting the toggle.
