# Change Brief: Multi-Device Responsive Container Layout Adaptation

## What changes
Implement multi-device responsive layout container adaptation for mobile phones, tablets, and desktop PC viewports. The container width will dynamically adjust across core layout components (Header, Landing page, Footer):
- Mobile phone viewports (<640px): `w-full px-4`
- Tablet viewports (≥640px & <1024px): `sm:px-6 sm:max-w-2xl md:max-w-4xl`
- Desktop PC viewports (≥1024px): `lg:max-w-6xl xl:max-w-7xl`

## Kind of change
`feature`

## Why this kind
Adding responsive layout adaptation across 3 distinct device tiers (mobile phone, tablet, desktop PC) introduces responsive breakpoint rules across layout components.

## Expected blast radius
- `Header` (`frontend/src/components/Header.tsx`): LOW risk.
- `Landing` (`frontend/src/pages/Landing.tsx`): LOW risk.
- `Footer` (`frontend/src/components/Footer.tsx`): LOW risk.
- `Layout` (`frontend/src/components/Layout.tsx`): LOW risk.
Callers and component hierarchy: `App` (`frontend/src/App.tsx`) renders `Routes`, which renders `Layout` (`frontend/src/components/Layout.tsx`). `Layout` structures `Header`, main route `<Outlet />` (rendering `Landing`), and `Footer`. Updating container width constraints affects horizontal alignment within this `App -> Layout -> (Header | Landing | Footer)` tree.

## Acceptance criteria
1. Mobile phone viewports (<640px) adapt to screen width with horizontal padding.
2. Tablet viewports (640px to 1024px) scale with side margins.
3. Desktop PC viewports (≥1024px) expand cleanly across desktop screens.
4. Automated unit tests (`npm test --prefix frontend -- --run`) and build (`npm run build --prefix frontend`) pass cleanly.

## Out of scope
- Modifying CSS theme color tokens or dark mode variables in `frontend/src/index.css`.
- Modifying component state, routing logic, or non-container component styles.

## Open questions
None.
