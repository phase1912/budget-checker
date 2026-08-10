# Implementation Note: User Authentication (JWT & Roles)

## Summary
Implements end-to-end user registration, authentication, token rotation, logout, role management, and header UI integration in Budget Checker using FastAPI (PyJWT + bcrypt) and Vite/React (MobX).

## Requirements implemented
- Registration with hashed passwords and role assignment (`/api/v1/auth/register`).
- Authentication with JWT Access (30 min) and Refresh (7 days) tokens (`/api/v1/auth/login`).
- Token rotation and revocation (`/api/v1/auth/refresh`, `/api/v1/auth/logout`).
- User profile endpoint (`/api/v1/auth/me`).
- FastAPI role-based access control dependency `require_role`.
- React `AuthModal` dialog with Sign In / Create Account tabs.
- React `UserDropdown` displaying user initials avatar, full name, email, role badge (`User` or `Admin`), settings, and logout.

## Symbols changed
- `User` model in `backend/app/models.py`: Added `email` index, `first_name`, `last_name`, `hashed_password`, `role`, `is_active`, `updated_at`, `refresh_tokens`.
- `RefreshToken` model in `backend/app/models.py`: Created model with `id`, `user_id`, `token_hash`, `expires_at`, `revoked`, `created_at`.
- `backend/app/security.py`: Added `hash_password`, `verify_password`, `hash_token`, `create_access_token`, `create_refresh_token`, `decode_token`.
- `backend/app/schemas.py`: Added `UserRegister`, `UserLogin`, `UserResponse`, `TokenResponse`, `RefreshTokenRequest`, `MessageResponse`.
- `backend/app/deps.py`: Added `get_current_user`, `get_current_active_user`, `require_role`.
- `backend/app/routers/auth.py`: Created router for `/register`, `/login`, `/refresh`, `/logout`, `/me`.
- `backend/app/main.py`: Included `auth.router`.
- `frontend/src/stores/AuthStore.ts`: Created MobX store managing auth state, token storage, API calls.
- `frontend/src/components/UserDropdown.tsx`: Created dropdown header component.
- `frontend/src/components/AuthModal.tsx`: Created auth modal component.
- `frontend/src/components/Header.tsx`: Integrated auth state and components into app header.

## Design notes
- Security: Passwords are hashed using bcrypt with salt. Refresh tokens are stored SHA-256 hashed in SQLite.
- JWT Claims: Standard claims include `sub` (User ID), `email`, `role`, `iat`, `exp`, `type`.
- UI Aesthetics: Uses modern Glassmorphism, smooth animations, dark/light theme integration, and Tailwind CSS.

## Risks
- Storage of access token in client storage. Mitigated by short 30-minute lifespan and server-side refresh token revocation.
