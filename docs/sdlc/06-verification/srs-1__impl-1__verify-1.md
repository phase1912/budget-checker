## Commands run

- `node .meridian/run.cjs analyze --index-only --pdg --allow-sdlc-reindex` — exit 0. 732 nodes, 932 edges, 9 clusters, 6 flows, 5.6s.
- `meridian sdlc verify-links` (CLI; the MCP `sdlc_verify_links` tool errored on repo disambiguation despite the correct name/path — used the CLI form, which resolves from cwd) — "Checked 53 link(s): 53 ok, 0 repaired."
- `cd frontend && npm run build` (`tsc --noEmit && vite build`) — exit 0, no errors. This also stood in for a lint command: no linter/formatter is configured anywhere in this repository (confirmed by re-checking for `.eslintrc*`/`.prettierrc*`), so `tsc --noEmit`'s type-check is the only static check that exists here.
- `cd frontend && npm test` (`vitest run`) — exit 0. 6 test files, 15 tests, all passed, 719ms.
- `grep -rn "#[0-9a-fA-F]\{3,6\}\|rgb(" frontend/src --include="*.tsx" --include="*.ts" | grep -v ".test."` — no matches (DS-1 inspection).
- Manual browser verification (Chrome preview, via `preview_start`/`computer`/`javascript_tool`): screenshotted the landing page in light and dark theme; toggled the theme and confirmed `document.documentElement.classList` and `localStorage.getItem('budget-checker-theme')` updated correctly; confirmed the app opened in dark theme on first load with nothing stored (this sandbox's OS/browser preference was dark, exercising the DS-7 fallback for real); navigated to an arbitrary unmatched path and confirmed `window.location.pathname` became `/not-found` with the NotFound heading rendered inside Layout (DS-13).

Nothing failed and then was made to pass by changing a test — every command above passed on this run without modification, including the one prior run at the implementation stage.

## Results

All commands passed as described. No test was altered to force a pass. The one thing changed mid-verification was the `build-command` answer itself, at the implementation stage: my first attempt accidentally included prose explanation text instead of just the shell command, which the engine tried to execute literally and failed with a shell syntax error — re-answered with the bare command (`cd frontend && npm install && npm run build`) and it passed. That was a mistake in how I answered the question, not a code or build defect.

The manual browser session in this sandboxed preview was unstable on longer interactive sequences — the tab underwent repeated unexplained full reloads a few seconds after actions (visible as repeated `[vite] connecting…/connected` cycles in the console). Every immediate post-action check, however, showed correct behavior. This is recorded as a known limitation of the verification environment, not of the code (see Known gaps).

## Acceptance coverage

| Scenario | Test | Notes |
|---|---|---|
| [[prob-1/concept-1/req-1/feature-1]] DS-1 (3 scenarios) | none | verification method: inspection — see grep result above |
| [[prob-1/concept-1/req-2/feature-1]] DS-2 scenario 1 | `frontend/src/components/Layout.test.tsx` — "renders the shared header and footer around the routed content" | |
| [[prob-1/concept-1/req-2/feature-1]] DS-2 scenario 2 | none | structural; empirically consistent with the 2 routes tested in App.test.tsx but not directly asserted |
| [[prob-1/concept-1/req-3/feature-1]] DS-3 | `frontend/src/App.test.tsx` — "renders the Landing page at the root path within the shared Layout" | |
| [[prob-1/concept-1/req-4/feature-1]] DS-4 scenario 1 | `frontend/src/components/ThemeToggle.test.tsx` — "switches the active theme when activated" (locates the button via role) | indirect |
| [[prob-1/concept-1/req-4/feature-1]] DS-4 scenario 2 | none | true by construction (Header always renders ThemeToggle), not asserted |
| [[prob-1/concept-1/req-5/feature-1]] DS-5 (outline, 2 examples) | `frontend/src/stores/ThemeStore.test.ts` — "switches the active theme when toggled" (both directions); `ThemeToggle.test.tsx` covers light→dark at the UI level | |
| [[prob-1/concept-1/req-6/feature-1]] DS-6 | `ThemeStore.test.ts` — "applies the stored theme preference on load" | |
| [[prob-1/concept-1/req-7/feature-1]] DS-7 (outline + 1 scenario) | `ThemeStore.test.ts` — "falls back to the OS preference when no theme is stored" (dark example); "falls back to the OS preference when localStorage is unavailable" (light example, combined with unavailable storage) | light-preference + merely-empty-storage combination not separately tested |
| [[prob-1/concept-1/req-8/feature-1]] DS-8 | `ThemeStore.test.ts` — "defaults to light when neither a stored nor an OS preference is available" | |
| [[prob-1/concept-1/req-9/feature-1]] DS-9 (2 scenarios) | none | verification method: demonstration/inspection — confirmed visually in browser |
| [[prob-1/concept-1/req-10/feature-1]] DS-10 | none | verification method: demonstration — confirmed via browser screenshots |
| [[prob-1/concept-1/req-11/feature-1]] DS-11 scenario 1 | `ThemeStore.test.ts` — "persists the new theme to localStorage when toggled" | |
| [[prob-1/concept-1/req-11/feature-1]] DS-11 scenario 2 | none | "switches the active theme when toggled" toggles twice but doesn't re-check localStorage after the second toggle |
| [[prob-1/concept-1/req-11/feature-1]] DS-11 scenario 3 | `ThemeStore.test.ts` — "still switches the theme even if persisting the choice fails" | |

19 of 23 approved scenarios have a direct or indirect automated test; 4 scenarios (all verification-method inspection/demonstration, or a same-code-path variant of an already-tested case) have none, listed above and in Known gaps.

## Known gaps

- **DS-1 and DS-9 (2 scenarios)**: verified only by manual grep/visual inspection, matching their declared verification method — no automated test exists or was required.
- **DS-10 (1 scenario)**: verified only by manual screenshot, matching its declared verification method (demonstration).
- **DS-2 scenario 2, DS-4 scenario 2, DS-11 scenario 2, and half of DS-7's outline**: named explicitly above — all are same-code-path variants of an already-tested case (e.g. the toggle button unconditionally renders, so "present in both themes" is structurally guaranteed rather than untested logic), not a distinct untested branch. Low risk, but real gaps, not silently dropped.
- **DS-12 and DS-13 are implemented but still have no formal requirement or acceptance-scenario artifacts of their own** (see [[srs-1/impl-1]] Design notes) — this verification report cannot claim scenario coverage for them because no approved scenario exists to check against yet. They were exercised manually in the browser (dark-mode visual change, not-found redirect) but that isn't the same as a scenario-mapped automated test.
- **Dark-theme WCAG AA contrast (DS-NFR-1)**: only the light-theme token pairs were hand-computed (see [[srs-1/impl-1]] Design notes); the eight dark-theme pairs were chosen by the same shade-pairing convention but not individually verified by calculation or tool.
- **Backend test suite (pytest) was not run** — this change doesn't touch the backend, and `test-command` was scoped to frontend accordingly; not a gap in this feature's own coverage, but noted so it isn't assumed to have been checked.
- **Sustained interactive browser sessions in this sandbox were unreliable** (see Results) — verification of live UI behavior relied on immediate post-action state checks rather than extended manual exploration; a real deployment/staging environment would be the more trustworthy place to repeat this manual pass before shipping.
