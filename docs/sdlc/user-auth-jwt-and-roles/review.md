# Code Review: User Authentication (JWT & Roles)

## Scope reviewed
- `backend/app/models.py`: `User` and `RefreshToken` SQLAlchemy models.
- `backend/app/security.py`: Password hashing with bcrypt, token generation and validation with PyJWT.
- `backend/app/schemas.py`: Pydantic authentication request and response models.
- `backend/app/deps.py`: Auth dependencies and role authorization middleware.
- `backend/app/routers/auth.py`: Auth REST endpoints (`/register`, `/login`, `/refresh`, `/logout`, `/me`).
- `backend/app/main.py`: Router integration.
- `backend/tests/test_auth.py`: Unit test suite.
- `frontend/src/stores/AuthStore.ts`: MobX store.
- `frontend/src/components/Header.tsx`, `AuthModal.tsx`, `UserDropdown.tsx`: Frontend React UI components.

## Findings
- **Security & Hashing**: Passwords are securely hashed with `bcrypt` salt. Refresh tokens are stored SHA-256 hashed in database to prevent plaintext leak if DB is compromised.
- **Role Enforcement**: `require_role` dependency correctly enforces role checks on protected endpoints.
- **UI Integrity**: `AuthModal` provides input validation, tab switching, and error alerts. `UserDropdown` cleanly presents user identity, role, and logout control.
- **Build & Tests**: Frontend builds without errors; backend test suite passes 100%.

## Blast radius
Modified symbols in `User` model, added `RefreshToken` model, added auth routes and frontend header components. Existing `Receipt` and `Budget` entities remain fully operational and unaffected.

## Residual risk
- Access token stored in `localStorage` client-side. Low residual risk due to short 30-minute token lifespan and server-side refresh token revocation on logout.

## Verdict
APPROVED. The implementation meets all functional requirements, quality attributes, and acceptance criteria.
