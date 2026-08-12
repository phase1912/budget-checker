# Pull Request: User Authentication (JWT & Roles)

URL: https://github.com/phase1912/budget-checker/pull/3

## Summary
This Pull Request delivers user registration, JWT authentication (Access & Refresh tokens with rotation and revocation), role-based access control (`user` and `admin`), and frontend header integration (AuthModal and UserDropdown) for Budget Checker.

## Requirements covered
- Registration with bcrypt password hashing and default role `user` (`/api/v1/auth/register`).
- Authentication with JWT Access (30 min) and Refresh (7 days) tokens (`/api/v1/auth/login`).
- Token rotation and revocation (`/api/v1/auth/refresh`, `/api/v1/auth/logout`).
- User profile endpoint (`/api/v1/auth/me`).
- Role-based FastAPI dependency `require_role`.
- Frontend AuthModal dialog with Sign In and Create Account forms.
- Frontend UserDropdown component with initials avatar, full name, email, role badge, settings, and logout option.

## Testing
- Automated pytest test suite (`backend/tests/test_auth.py`): 2 passed in 0.67s.
- Frontend compilation (`npm --prefix frontend run build`): `tsc --noEmit && vite build` passed cleanly.
- Code index and graph validation (`1,425 nodes | 2,067 edges`).

## Risk and blast radius
- Blast radius is strictly confined to authentication entities, routers, schemas, dependencies, and frontend header components. Existing receipts and budgets functionality remains fully operational.
