# Problem Brief: User Authentication (JWT & Roles)

## Problem
In the Budget Checker application, user authentication and registration are not implemented. Users cannot create accounts, sign in securely, or manage personal budgets. All application data currently lacks authentication and authorization protection.

## Who is affected
New and existing users of the Budget Checker system who require private access to their personal budget data and role-based permissions (User / Admin).

## Evidence
In the current master branch codebase:
- `backend/app/models.py` contains only a minimal `User` model without password hashes, tokens, or roles.
- `backend/app/routers/` contains no authentication endpoints.
- `frontend/src/components/` lacks authentication modal dialogs and user account headers/dropdowns.

## Cost of inaction
User budget data remains unprotected and public. Individual user workspace isolation, profile management, and administrative role enforcement cannot be developed.

## Success metrics
1. Users can register with email, first name, last name, password, and confirm password.
2. Users can log in using email and password, receiving JWT Access and Refresh tokens.
3. Authenticated state is displayed in the header with a user avatar icon and dropdown menu (showing name, email, role, settings, and logout).
4. Unauthenticated users see a "Log In" button opening an authentication modal dialog with Sign In / Create Account tabs.
5. Logout revokes the session and clears local client state.
6. Backend endpoints for authentication (`/api/v1/auth/register`, `/login`, `/refresh`, `/logout`, `/me`) are fully functional and protected.

## Out of scope
1. Password reset flow ("Forgot Password").
2. Email verification and confirmation emails.
3. Multi-factor authentication (2FA).
4. Social OAuth logins (Google, GitHub).

## Assumptions
- Password hashing uses `bcrypt` with standard cost factor.
- JWT tokens follow RS256 / HS256 standard with 30-minute Access Token expiration and 7-day Refresh Token expiration.
- Roles currently default to `user`, with support for `admin` role checking in dependencies.

## Open questions
None at this stage. All requirements for basic user authentication and roles are confirmed.
