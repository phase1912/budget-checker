# Solution Concept: Frontend Design System Foundation

Derived from [[prob-1]], specifically the [[prob-1]] "SPA/shared-layout" assumption and the founder's success metrics (single source of truth for color, redesigned landing page, working dark-mode toggle).

## Options considered

### Option A — Do nothing (baseline)

Leave `frontend/src/pages/Landing.tsx` as bare unstyled JSX. Costs nothing today. Rejected as the actual plan, but kept as the reference point: this is exactly the state [[prob-1]] describes as the problem, and its "Cost of inaction" section is the argument against it — technical debt keeps compounding as more screens are added.

### Option B — Minimal Layout, no router

Add Tailwind + design tokens, wrap `<Landing/>` in a `Layout` component (header + footer + content slot) directly inside `App.tsx`, with no routing library. Cheapest option that still satisfies the SPA/shared-chrome requirement for exactly one page. Cost: roughly 1 day less than Option C, since there's no router to wire up. Gives up: nothing today, but the moment a second real page exists, `App.tsx` has to be restructured to introduce a router and re-home the `Layout` as its root — the exact rework [[prob-1]]'s "Cost of inaction" section warns about, just deferred one layer.

### Option C — Router-ready foundation (chosen)

Same Tailwind + token work as Option B, plus `react-router` added now: `Layout` becomes the root layout route (an `<Outlet/>` for content), with a single route (`/`) rendering `Landing` today. Cost: one extra dependency and roughly half a day of routing setup on top of Option B, still comfortably inside the founder's "a few days" appetite. Gives up: marginally more code to review today for a capability (routing) not yet used by a second page.

## Chosen approach

Option C. Concretely:

- **Tokens**: a Tailwind v4 theme (CSS-first `@theme` block, via the official `@tailwindcss/vite` plugin) defines the full color system — green primary/success, indigo accent, semantic error/warning/info, and a neutral gray scale — plus light/dark variants, as CSS custom properties. This is the "one place" the founder asked for: no component defines its own color value.
- **Layout**: `react-router` is added with `Layout` as the root layout route (rendering the shared header + footer around an `<Outlet/>`), and a single route mounting `Landing` at `/`. Header contains the dark-mode toggle.
- **Dark mode**: implemented via a `dark` class on `<html>` toggled by the header control, with token CSS variables overridden under `.dark`; the choice persists in `localStorage` and is read on load to avoid a flash of the wrong theme.
- **Icons**: `lucide-react` supplies the toggle icon (and any other UI icons this feature needs) instead of a hand-built SVG sprite.
- **Landing page**: redesigned to use the new header/footer/tokens instead of bare JSX, closing the founder's success metric on landing-page redesign.

This does not specify component file layout, token naming, or the exact route table — that is requirements/design work for the next stage.

## Why not the alternatives

**Option A (do nothing):** directly contradicts the problem this feature exists to solve — [[prob-1]] establishes that leaving the frontend unstyled has a real, growing cost, and the founder's own success metrics require a shipped color system and redesigned landing page, neither of which "do nothing" produces.

**Option B (minimal Layout, no router):** saves perhaps half a day now but reintroduces the exact kind of rework [[prob-1]]'s Assumptions section flags — the founder was specific that header/footer must be shared SPA chrome, and the cheapest way to guarantee that stays true as pages are added is to let the router own the layout boundary from the start, not retrofit it later. Given the founder's confirmed appetite ("a few days") comfortably covers the extra half-day, and reversibility is confirmed to be high either way, there's no real upside to deferring it.

**Tailwind v3 (rejected sub-choice within the chosen option):** more mature ecosystem and more existing tutorials, but requires a separate `tailwind.config.ts` plus PostCSS/autoprefixer wiring. Tailwind v4's CSS-native `@theme` and its official Vite plugin is less configuration surface for a project with strict TypeScript and no existing PostCSS pipeline to preserve, and CSS-variable-based tokens map directly onto the dark-mode variable-override approach chosen here.

**Custom SVG sprite (rejected sub-choice within the chosen option):** gives full control over icon appearance, but means drawing or sourcing every icon by hand for a "few days" appetite feature. `lucide-react` is tree-shakeable, has official React components, and already covers the icons this feature needs (theme toggle, and whatever the landing redesign turns out to want).

## Constraints

- No deadline, no dependency budget, no mandated Tailwind version, no hosting/deploy requirement — founder confirmed "no constraints — full freedom" (answer to `constraints`).
- Appetite is "a few days" (answer to `appetite`) — this ruled out heavier options like building a full component-library package or a custom design-tooling pipeline, neither of which was seriously considered given that budget.

## Assumptions

- The `frontend/package.json` toolchain (Vite, React 18, TypeScript, MobX, Vitest) stays as-is; nothing here requires a framework change. *Cheap to check now* — confirmed by reading `package.json` directly.
- `react-router`'s current major version integrates cleanly with Vite + React 18 + strict TypeScript with no special configuration. *Cheap to check now* — should be verified during implementation by actually installing and building, not assumed indefinitely.
- Tailwind v4's `@tailwindcss/vite` plugin needs no PostCSS config of its own, since none exists in this project to conflict with. *Cheap to check now.*
- Dark mode via a `.dark` class + CSS variable overrides will be sufficient for this feature's scope (landing page only); it is not yet known whether this pattern holds up once authenticated app screens exist. *Only discoverable later*, explicitly out of scope for this feature per [[prob-1]].

## Risks

- **Tailwind v4 is newer** than v3; less community troubleshooting content exists if something in the Vite plugin misbehaves. Early sign it's a problem: the dev server or build fails when wiring the plugin in — if that happens for more than an hour of debugging, falling back to Tailwind v3 is cheap given confirmed high reversibility.
- **Introducing a router for one page** could look like premature architecture to a future reviewer. Mitigated by [[prob-1]]'s explicit SPA/shared-layout assumption, which the founder confirmed came from a deliberate architectural decision, not a guess.
- **Dark mode scope creep**: "full dark theme" could expand to cover interactions this feature didn't anticipate (e.g. form controls, focus states) if the landing page redesign turns out more elaborate than expected. Early sign: implementation taking noticeably longer than the "few days" appetite — should trigger a check-in rather than silently expanding scope.

## Out of scope

Carried forward from [[prob-1]]: auth/login on the landing page (separate feature), authenticated/internal app screens (don't exist yet), i18n/localization, non-essential animation.

Newly excluded by this concept: any component library or design-tooling package beyond Tailwind config + a handful of shared components (Layout, Header, Footer, ThemeToggle) — building a general-purpose UI kit is bigger than "a few days" and isn't what the founder asked for.
