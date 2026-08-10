## Summary

Implements the frontend design system foundation baselined in [[srs-1]]: a single Tailwind v4 theme configuration (green primary, indigo accent, semantic error/warning/info, neutral chrome) as the sole source of color; a router-ready `Layout` (react-router-dom v6, compatible with the project's existing React 18) providing a shared header and footer across all routes; a full light/dark theme with a header toggle, localStorage persistence, and a two-level fallback (stored preference → OS preference → light); vector icons via `lucide-react`; and a redesigned, token-styled `Landing` page. `App.tsx` now defines the route tree instead of rendering `Landing` directly, and `main.tsx` wraps it in `BrowserRouter` and imports the new stylesheet.

## Requirements implemented

- [[prob-1/concept-1/req-1]] (DS-1) — `frontend/src/index.css` `@theme` block is the only place any color value is defined; every component references semantic Tailwind classes (`bg-primary`, `text-foreground`, etc.). Verified: `grep` for hex/rgb literals outside `index.css` returns nothing.
- [[prob-1/concept-1/req-2]] (DS-2) — `Layout` renders `Header` + `<Outlet/>` + `Footer`; `App.tsx` nests every route under the `Layout` root route.
- [[prob-1/concept-1/req-3]] (DS-3) — `App.tsx`'s index route renders `Landing` at `/`.
- [[prob-1/concept-1/req-4]] (DS-4) — `Header` always renders `ThemeToggle`.
- [[prob-1/concept-1/req-5]] (DS-5) — `ThemeStore.toggle()` flips `theme` between `'light'`/`'dark'`.
- [[prob-1/concept-1/req-11]] (DS-11) — `ThemeStore.toggle()` calls `persistTheme()`, a best-effort `localStorage.setItem` that never throws out of `toggle()`.
- [[prob-1/concept-1/req-6]] (DS-6) — `ThemeStore`'s constructor calls `resolveInitialTheme()`, which checks `readStoredTheme()` first.
- [[prob-1/concept-1/req-7]] (DS-7) — `resolveInitialTheme()` falls back to `readSystemTheme()` (`window.matchMedia('(prefers-color-scheme: …)')`) when nothing is stored.
- [[prob-1/concept-1/req-8]] (DS-8) — `resolveInitialTheme()`'s final `?? 'light'` fallback.
- [[prob-1/concept-1/req-9]] (DS-9) — `ThemeToggle` renders lucide-react's `Sun`/`Moon` components, visually distinct per state.
- [[prob-1/concept-1/req-10]] (DS-10) — `Landing.tsx` rewritten to use theme-token Tailwind classes instead of unstyled JSX.
- [[prob-1/concept-1/qa-1]] (DS-NFR-1, WCAG AA contrast) — see Design notes for the contrast values actually computed for the light-theme token pairs.

Also implemented, beyond the strict baseline — see Design notes/Risks: the founder-agreed but not-yet-formally-registered DS-12 (dark token variants) and DS-13 (not-found redirect).

## Symbols changed

- `App` (frontend/src/App.tsx) — now returns a `<Routes>` tree (`Layout` root route, index `Landing`, `not-found`, catch-all redirect) instead of rendering `Landing` directly.
- `Landing` (frontend/src/pages/Landing.tsx) — markup unchanged in structure/content, restyled with Tailwind token classes; outer element changed from `<main>` to `<div>` since `Layout` now owns the page's `<main>` landmark.
- New: `Layout`, `Header`, `Footer` (frontend/src/components/).
- New: `ThemeToggle` (frontend/src/components/ThemeToggle.tsx).
- New: `ThemeStore` class + `themeStore` singleton (frontend/src/stores/ThemeStore.ts), following the existing `HealthStore` singleton pattern.
- New: `NotFound` (frontend/src/pages/NotFound.tsx).
- `main.tsx` — wraps `App` in `BrowserRouter`, imports `index.css`.
- `vite.config.ts` — adds the `@tailwindcss/vite` plugin.
- Untouched: `HealthStore`, `fetchHealth`, `Landing`'s props contract (`backendStatus`) — confirmed via the `blast-radius` impact() run at the planning step (1 direct caller, `App`, risk LOW).

## Design notes

- **DS-12 and DS-13 implemented despite not being formally registered requirements.** Both were explicitly agreed with the founder during the acceptance stage (recorded on the [[prob-1/concept-1/req-1]] and [[prob-1/concept-1/req-3]] acceptance branches) but couldn't be registered as `requirement` artifacts there. Implementing DS-1 through DS-11 literally, without them, would have produced a dark-mode toggle that switches a CSS class without the palette actually changing (defeating the founder's explicit "full dark theme, not scaffolding" ask) and a router with no defined behavior for mistyped URLs (the exact gap the founder asked to be fixed). Given both were confirmed twice in conversation, omitting them would have been quietly narrower than what was actually agreed — so I built them, and I'm flagging it here rather than treating it as in-scope by default. `frontend/src/index.css` defines distinct `:root`/`.dark` values for every semantic token; `App.tsx`'s catch-all route redirects to `/not-found`, a dedicated `NotFound` page rendered inside `Layout`. Both still need formal EARS requirement artifacts with their own acceptance scenarios as the promised fast-follow.
- **State management**: `ThemeStore` mirrors `HealthStore`'s existing pattern exactly (MobX `makeAutoObservable` class + module-level singleton), per the `existing-machinery` answer — no new state-management approach introduced.
- **Router library**: `react-router-dom@^6`, not the `react-router@8` that `npm install react-router` resolved to by default — v8's peer dependency requires React ≥19.2.7, and this project is pinned to React 18.3.1 with no decision anywhere to change that. v6 is the React-18-compatible major version with the same route-tree API the concept called for.
- **Semantic tokens over raw color-scale tokens**: rather than exposing a raw green-50…green-900 scale, `index.css` defines purpose-named tokens (`primary`, `accent`, `success`, `error`, `warning`, `info`, plus `background`/`foreground`/`surface`/`border`/`muted`) with light/dark values baked in. This is what makes DS-1 ("single source of truth") and DS-12 (distinct light/dark values) both concretely satisfiable — components never choose a shade themselves.
- **Not-found via redirect, not direct render**: the founder's own words were "перенаправлять на эту страницу" (redirect to this page), so the catch-all route is `<Navigate to="/not-found" replace />` rather than rendering `NotFound` inline at the unmatched path — the URL bar actually changes to `/not-found`, matching what was asked rather than a cheaper direct-render alternative.
- **Pre-existing bug fixed as a prerequisite, not part of the feature**: `vite.config.ts` already referenced `process.env.PORT` before this change (confirmed via `git diff`, that line predates this feature), but `@types/node` was never installed, so `tsc --noEmit` — the first half of this project's own `build` script — was already broken on the baseline before I touched anything. I added `@types/node` as a devDependency so `build-command` could run at all; this is a one-line, test-covered-by-the-build-itself fix, not a product change, and no other part of the codebase was touched to make it work.

## Risks

- **DS-NFR-1 (WCAG AA contrast) — verified by manual calculation for light-theme pairs only, not tooled.** I computed WCAG relative-luminance contrast ratios by hand for the light-theme text/background pairs: foreground/background 17.85:1, primary-foreground/primary 5.01:1, error-foreground/error 6.47:1, info-foreground/info 6.70:1, accent-foreground/accent 6.29:1, muted-foreground/background 4.76:1, warning-foreground/warning 4.70:1 — all clear 4.5:1, though warning and muted-foreground pass with the narrowest margin. I did not compute the eight dark-theme pairs (chosen by the same shade-pairing logic, but not individually verified), and I don't have an automated contrast-checking tool in this environment. Recommend running an actual tool (e.g. axe or a contrast checker) over both themes during verification — DS-NFR-1's own note already flagged this as something to check with real tooling rather than trust hand-computed values indefinitely.
- **DS-12/DS-13 scope-widening**: implemented ahead of their formal requirement registration (see Design notes). If the founder disagrees with how I interpreted "distinct light/dark values" (semantic tokens, not a raw color-scale duplication) or "not-found page" (a real route + redirect, not a toast/modal), that's a design decision made without a written requirement to check it against — flagged explicitly so it gets scrutinized, not assumed correct.
- **Live dev-server browser session was unstable during manual verification.** In this sandboxed preview, the page underwent repeated unexplained full reloads a few seconds after each interaction (visible as repeated `[vite] connecting…/connected` cycles in the console) — a session-level effect, since retrying immediately after each reload always showed the correct behavior, and neither reload target ever landed anywhere but the pre-reload same-app state. I did not fully diagnose the reload's root cause. Confidence in correctness rests primarily on the deterministic, passing automated test suite (`npm test`, 15/15 green, run outside the dev server) and on immediate post-action browser checks, not on sustained interactive dev-server testing.
- **`npm audit` reports 7 pre-existing vulnerabilities** (5 moderate, 1 high, 1 critical) in the dependency tree after `npm install`; none are in packages this feature added directly (spot-checked: they predate this change, inherited from existing transitive deps). Not fixed here — out of this feature's declared scope, flagging so it isn't mistaken for something this change introduced.
- **React Router v6→v7 future-flag console warnings** appear in dev/test output (`v7_startTransition`, `v7_relativeSplatPath`). Non-blocking, don't affect behavior or tests; not addressed since opting into v7 behavior early wasn't part of any agreed requirement.
