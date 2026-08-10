# Solution Concept: User Authentication (JWT & Roles)

## Options considered
1. **Option A: Custom JWT Authentication with Refresh Token Rotation (Chosen)**
   - Backend: FastAPI, SQLAlchemy models (`User`, `RefreshToken`), bcrypt password hashing, PyJWT tokens (Access Token 30 min, Refresh Token 7 days).
   - Frontend: Vite + React + TypeScript + MobX (`AuthStore`), `AuthModal` dialog, `UserDropdown` header menu.
2. **Option B: Session-based Cookie Authentication**
   - Stateful session cookies stored in SQLite/Redis.
   - Requires state management on backend and server-side session lookup for every request.
3. **Option C: External SaaS Authentication (Auth0 / Firebase)**
   - Delegating authentication to a third-party service.
   - Increases external dependencies and API latency, requires external credentials.

## Chosen approach
We select **Option A (Custom JWT Authentication)**.
- **Data Model**:
  - `User`: `id` (UUID), `email` (unique index), `first_name`, `last_name`, `hashed_password` (bcrypt), `role` (`"user"` / `"admin"`), `is_active`, `created_at`, `updated_at`.
  - `RefreshToken`: `id`, `user_id` (foreign key to `users.id`), `token_hash` (SHA-256), `expires_at`, `revoked` (boolean), `created_at`.
- **Backend Architecture**:
  - `backend/app/security.py`: Password hashing & verification, token creation (`create_access_token`, `create_refresh_token`), token decoding.
  - `backend/app/deps.py`: `get_current_user`, `get_current_active_user`, `require_role(role)` FastAPI dependencies.
  - `backend/app/routers/auth.py`: REST endpoints `/register`, `/login`, `/refresh`, `/logout`, `/me`.
- **Frontend Architecture**:
  - `frontend/src/stores/AuthStore.ts`: MobX store for auth state, automatic token refresh, token storage in `localStorage`.
  - `frontend/src/components/Header.tsx`: Navigation bar with "Log In" button or user avatar dropdown.
  - `frontend/src/components/AuthModal.tsx`: Modal dialog for Sign In and Create Account (email, first/last name, password, password confirmation).
  - `frontend/src/components/UserDropdown.tsx`: Dropdown showing user full name, email, role badge (`User` or `Admin`), Settings, and Logout button.

## Why not the alternatives
- **Option B (Session-based)**: Requires stateful backend session management, making client-side REST calls and MobX state persistence less flexible compared to standard Bearer JWT headers.
- **Option C (External SaaS)**: Introduces vendor lock-in, external network overhead, and complex local development setup for a core Budget Checker feature.

## Constraints
- Must integrate seamlessly with the existing FastAPI backend and Vite/React frontend stack.
- Must run locally with SQLite database without external auth SaaS dependencies.
- Password hashing must use secure `bcrypt` algorithm.

## Assumptions
- JWT Access tokens expire in 30 minutes; Refresh tokens expire in 7 days.
- User roles default to `"user"`, with `"admin"` reserved for elevated permissions.
- Password minimum length is 6 characters.

## Risks
- **Token Storage**: Storing tokens in `localStorage` carries potential XSS risk if third-party scripts are introduced later. Mitigation: Strict input sanitization, clean dependencies, and future migration option to HTTP-only cookies if required.

## Out of scope
- Password reset via email link.
- Email address verification.
- Two-factor authentication (2FA).
- OAuth social logins.
