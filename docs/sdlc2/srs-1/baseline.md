## Purpose

This document is the requirements baseline for the "Frontend design system" feature — centralized color tokens, a router-ready shared Layout (header/footer), a light/dark theme toggle, and a redesigned landing page. Design and implementation are committed against exactly what is recorded here: every functional requirement, quality attribute, and acceptance scenario below is an approved artifact, copied verbatim, not restated.

## Scope

In scope (from [[prob-1]] and [[prob-1/concept-1]]): a single centrally-maintained color theme (Tailwind v4), a router-ready `Layout` component providing shared header/footer across routes, a full light/dark theme with a toggle in the header (persisted, with a two-level fallback), vector UI icons, and a redesigned public landing page.

Out of scope (from [[prob-1]]): authentication/login on the landing page (deferred to a separate feature — the backend has no auth infrastructure at all), any authenticated/internal app screens (none exist yet), i18n/localization, and non-essential animation.

## Definitions

A scan of all 11 requirements and the one quality attribute found no domain terms of the ambiguous "valid/active/expired/eligible" class — see the `undefined-terms` answer on this stage. The terms below are defined for a reader outside this process, not because they were ambiguous within it:

- **Theme configuration** — the single, centrally maintained definition of every color used in the UI (implemented as a Tailwind v4 theme), referenced by components rather than hard-coded.
- **Token** — one named color entry within the theme configuration (e.g. "primary", "error"), with a distinct value per theme variant.
- **Layout** — the shared component that renders the header and footer around whatever route is currently active; the root layout route in the router.
- **Theme toggle** — the control in the header that switches the active theme between light and dark.
- **Stored preference** — the visitor's theme choice as persisted in `localStorage`, read back on subsequent visits.

## Functional requirements

### DS-1 — Single source of truth for color tokens
- **Statement (ubiquitous):** The frontend shall define every color value used in the UI within a single, centrally maintained theme configuration.
- **Priority:** must · **Verification:** inspection

### DS-2 — Shared Layout renders header and footer
- **Statement (ubiquitous):** The application shall render a shared header and footer around the content of every route through a single Layout component.
- **Priority:** must · **Verification:** demonstration

### DS-3 — Router mounts Landing at root path
- **Statement (ubiquitous):** The router shall mount the Landing page as the content of the Layout at the root path.
- **Priority:** must · **Verification:** test

### DS-4 — Header exposes theme toggle
- **Statement (ubiquitous):** The header shall provide a control that toggles the application between light and dark theme.
- **Priority:** must · **Verification:** demonstration

### DS-5 — Theme toggle switches the active theme
- **Statement (event-driven):** When the user activates the theme toggle, the application shall switch the active theme between light and dark.
- **Priority:** must · **Verification:** test

### DS-6 — Apply stored theme preference on load
- **Statement (event-driven):** When the application loads, the application shall apply the theme stored in localStorage if a stored preference exists.
- **Priority:** must · **Verification:** test

### DS-7 — Fallback to OS theme preference
- **Statement (unwanted-behaviour):** If localStorage is unavailable or contains no stored theme preference, then the application shall apply the operating system's prefers-color-scheme setting.
- **Priority:** must · **Verification:** test

### DS-8 — Default to light theme
- **Statement (unwanted-behaviour):** If neither a stored theme preference nor an operating system color-scheme preference is available, then the application shall apply the light theme.
- **Priority:** must · **Verification:** test

### DS-9 — UI icons rendered as vector graphics
- **Statement (ubiquitous):** The application shall render every UI icon, including the theme toggle icon, as a vector graphic that visually distinguishes each icon's meaning.
- **Priority:** must · **Verification:** inspection

### DS-10 — Landing page styled with token palette
- **Statement (ubiquitous):** The Landing page shall present its content styled with the Tailwind theme tokens instead of the current unstyled markup.
- **Priority:** must · **Verification:** demonstration
- **Note:** this statement names "Tailwind" specifically — the same implementation-detail leak that was caught and fixed in DS-1 and DS-9 during their review pass, but missed for DS-10 at the time. Per this stage's instruction to copy approved requirements verbatim rather than rewrite them, the wording is reproduced as approved; the fix is listed under Open questions and assumptions as a fast-follow.

### DS-11 — Theme toggle persists choice to localStorage
- **Statement (event-driven):** When the user activates the theme toggle, the application shall persist the resulting theme to localStorage.
- **Priority:** must · **Verification:** test

## Quality attributes

### DS-NFR-1 — WCAG AA contrast for token palette
- **Statement (state-driven):** While the color token palette is used to render text against a background, the frontend shall maintain a contrast ratio that meets WCAG 2.1 AA.
- **Metric:** contrast ratio between each token's foreground/text color and its intended background color
- **Threshold:** at least 4.5:1 for normal-size text, at least 3:1 for large-scale text
- **Conditions:** evaluated for every token pairing intended for text-on-background use, in both the light and dark theme variants
- **Priority:** must · **Verification:** analysis
- **Note:** the 4.5:1 figure was shown to and explicitly selected by the founder. The 3:1 large-text companion figure is the standard WCAG 2.1 AA pairing, added by the maker when drafting this artifact and not separately confirmed — see Open questions and assumptions.

## Acceptance scenarios

Each requirement's Gherkin scenarios are lifted verbatim into their own feature file:

| Requirement | Feature file |
|---|---|
| DS-1 | `features/DS-1.feature` |
| DS-2 | `features/DS-2.feature` |
| DS-3 | `features/DS-3.feature` |
| DS-4 | `features/DS-4.feature` |
| DS-5 | `features/DS-5.feature` |
| DS-6 | `features/DS-6.feature` |
| DS-7 | `features/DS-7.feature` |
| DS-8 | `features/DS-8.feature` |
| DS-9 | `features/DS-9.feature` |
| DS-10 | `features/DS-10.feature` |
| DS-11 | `features/DS-11.feature` |

DS-NFR-1 has no feature file: it is a quality attribute verified by `analysis`, which legitimately has no Gherkin scenario.

## Traceability matrix

See `traceability-matrix.md`.

## Open questions and assumptions

- **DS-12 (not yet a registered requirement) — dark-variant token coverage.** Agreed with the founder while analyzing DS-1 during acceptance: "The theme configuration shall define a distinct value for both the light and dark variant of every color token used in the UI." This closes a real gap — DS-4 through DS-8 govern the toggle's mechanics, but nothing previously required the palette to actually differ between themes. It could not be registered as a formal `requirement` artifact from within the acceptance stage (that stage only accepts `acceptance_spec`). The founder confirmed baselining now with this named as an open gap, to be formally added — with its own acceptance scenario — in a fast-follow pass before implementation touches dark-mode token values.
- **DS-13 (not yet a registered requirement) — not-found page for unmatched routes.** Agreed with the founder while analyzing DS-3: introducing a router means an unmatched path (typo, stale bookmark) is now reachable where it wasn't before. The founder wants a dedicated not-found page, with unmatched routes redirecting to it, rendered inside the shared Layout. Same registration limitation as DS-12 applies; same fast-follow commitment.
- **DS-10 wording.** Names "Tailwind" directly in its EARS statement, an implementation detail that should have been generalized the way DS-1 and DS-9 were. Reproduced verbatim per this stage's rules; fix alongside DS-12/DS-13.
- **DS-NFR-1's 3:1 large-text threshold.** Proposed by the maker as the standard WCAG 2.1 AA companion to the founder-confirmed 4.5:1 normal-text figure, not separately shown to or confirmed by the founder. Should be treated as an assumption until explicitly confirmed.
- **No other hedged or unresolved answers were found** across any stage — every other question was answered decisively by the founder (see `unresolved-questions` on this branch and the recorded decisions in `sdlc_history`).
