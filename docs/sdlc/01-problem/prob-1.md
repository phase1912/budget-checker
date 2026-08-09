# Problem Brief: Frontend Design System

## Problem

The frontend has no shared styling foundation. Colors, spacing, and component look-and-feel are not defined anywhere central, so there is no single place to answer "what is our primary color" or "what does a button look like here" — each new piece of UI would have to invent its own answer from scratch. The one screen that exists today, the public landing page, currently ships as unstyled markup with no visual design applied at all.

## Who is affected

End users of the public landing page. This is a solo project — the founder is the only developer — so the immediate audience for "no design system" is whoever visits the landing page and sees unstyled HTML, not a separate team of contributors (there isn't one yet). The founder did not have a frequency or count to attach to this (no traffic/analytics were cited).

## Evidence

Evident directly from the repository, not from a metric or complaint (founder confirmed this explicitly): no `.css` files exist anywhere under `frontend/`, no `tailwind.config`, no `postcss.config`, no design-tokens file. `frontend/src/pages/Landing.tsx` is plain JSX with one unstyled class (`status`) that has no matching stylesheet — confirmed by reading the file directly.

## Cost of inaction

Founder's own answer: technical debt keeps growing. Every new screen or component built before a central system exists gets its own ad-hoc styling, which then has to be redone once a real system is introduced — that rework is the specific cost, and it is avoided by establishing the system now while the frontend is still a single page rather than after more screens exist.

## Success metrics

Founder's own framing, made concrete:
- **Single source of truth for color** — measurable today: grep the frontend for raw hex/rgb color values outside the Tailwind theme config; it should return nothing.
- **Landing page redesigned with header and footer** — measurable by visual inspection: the page currently has neither.
- **Working light/dark theme toggle in the header, persisted across visits** — measurable by testing: toggle the theme, reload the page, confirm the choice held (e.g. via `localStorage`).

## Out of scope

- **Auth/login on the landing page.** A reasonable person building a "design system + landing page" feature might expect a login form to be part of it, since the founder originally raised it in the same conversation — but it is explicitly deferred to a separate feature. The backend has no auth infrastructure at all (no password field on `User`, no login endpoint, no session/JWT handling), so building it is a distinct, larger effort.
- **Authenticated/internal app screens** (dashboard, budgets, receipts) — these don't exist yet in the frontend, so extending the design system to them is not part of this feature; only the token foundation and the public landing page are.
- **i18n/localization and animation beyond what the redesign itself needs** — not part of this feature.

Explicitly **in scope** (flagged because it was initially proposed as out-of-scope and the founder reversed that): a full dark theme, not just token scaffolding, with a working toggle in the header, plus an icon set for UI icons — starting with the toggle button itself — using either a small custom SVG sprite or a library such as `lucide-react` (founder is open to either; to be decided during implementation/requirements).

## Assumptions

- Tailwind CSS is the styling tool (founder specified this explicitly; not up for reconsideration in this feature).
- Primary brand color is green, with indigo as the chosen secondary/accent color (confirmed by the founder in conversation), plus a standard semantic set (error/warning/info) and a neutral gray scale for chrome.
- The project is Vite + React + TypeScript + MobX (per `frontend/package.json`); no framework change is implied by this feature.
- "All colors in one place" means a Tailwind theme/token configuration, not necessarily a single physical file — one authoritative source that all components reference.
- **The application is a single-page application (SPA).** The founder clarified this after reviewing the draft: header and footer are shared/persistent chrome, not per-page markup — only the content area changes between views. This feature must produce a `Layout` (or equivalent) component that wraps routed content with a single shared header and footer, rather than baking header/footer into the `Landing` page itself. Today there is only one page (`Landing`) and no router configured; the requirements stage must decide whether to introduce a router now (e.g. `react-router`) to make the shared-layout structure real, or to structure `App.tsx` so a router can be dropped in later without reshuffling the layout.

## Open questions

None outstanding — every required question for this stage was answered by the founder in conversation (see question log above) or resolved by direct repository investigation (`prior-attempts`). The SPA/shared-layout clarification is captured above as an assumption to carry into the requirements stage, per the founder's explicit request.
