# Baseline Brief: User Authentication (JWT & Roles)

## Purpose
This baseline defines the functional specification, quality attributes, acceptance scenarios, and traceability matrix for user registration, JWT authentication, token rotation, and role-based access control in Budget Checker.

## Scope
- Registration (`/api/v1/auth/register`) with email, password, name fields.
- Authentication (`/api/v1/auth/login`) returning Access (30 min) and Refresh (7 days) tokens.
- Token rotation (`/api/v1/auth/refresh`) and revocation (`/api/v1/auth/logout`).
- User profile fetching (`/api/v1/auth/me`).
- Role assignment (`user`, `admin`) and FastAPI `require_role` dependency.
- Frontend AuthModal (Sign In / Create Account) and UserDropdown header menu.

## Definitions
- **JWT (JSON Web Token)**: Standard token format (RFC 7519) signed with HS256 algorithm.
- **Access Token**: Short-lived (30 minutes) bearer token containing user identity claims (`sub`, `email`, `role`).
- **Refresh Token**: Long-lived (7 days) token stored hashed in the `refresh_tokens` database table, used to acquire new access tokens.
- **RBAC (Role-Based Access Control)**: Authorization system checking user role (`user` vs `admin`) on backend dependencies.

## Functional requirements
1. **Registration**: Accepts email, password, first_name, last_name; hashes password via bcrypt; creates user record with default role `user`; returns token payload.
2. **Authentication**: Validates email and bcrypt password hash; creates session refresh token record in DB; returns JWT tokens.
3. **Token Refresh**: Accepts valid non-revoked refresh token; revokes old refresh token; issues new access and refresh token pair.
4. **Logout**: Revokes specified refresh token in DB and clears client tokens.
5. **Role-Based Access**: Restricts admin-only endpoints to users having `role == "admin"`.

## Quality attributes
1. **Latency**: Authentication and registration endpoints respond within < 200 ms.
2. **Security**: Passwords are never stored in plaintext and passwords are never logged in application logs.
3. **Token Expiration**: Access token expires strictly after 30 minutes; Refresh token expires strictly after 7 days.

## Acceptance scenarios
1. **Scenario 1 (Successful Registration)**:
   - Given a guest user submits valid email `test@example.com` and password `Password123!`.
   - Then a new user is created in database with role `user`.
   - And the response HTTP status is 201 with access_token and refresh_token.
2. **Scenario 2 (Invalid Login)**:
   - Given a user attempts login with incorrect password.
   - Then response status is 401 Unauthorized with detail message.
3. **Scenario 3 (Token Rotation & Logout)**:
   - Given an authenticated user calls `/api/v1/auth/refresh` with a valid refresh token.
   - Then a new token pair is returned and old refresh token is marked revoked.
   - When user calls `/api/v1/auth/logout`, the refresh token cannot be reused.
4. **Scenario 4 (Admin Role Enforcement)**:
   - Given a user with role `user` attempts to access an endpoint protected by `require_role("admin")`.
   - Then response status is 403 Forbidden.

## Traceability matrix
| Requirement | Concept | Problem | Acceptance Scenario |
| ----------- | ------- | ------- | ------------------- |
| User Registration | [[concept-1]] | [[problem-1]] | Scenario 1 |
| User Authentication | [[concept-1]] | [[problem-1]] | Scenario 2 |
| Token Refresh & Logout | [[concept-1]] | [[problem-1]] | Scenario 3 |
| Role-based Access | [[concept-1]] | [[problem-1]] | Scenario 4 |

## Open questions and assumptions
- Passwords must be at least 6 characters in length.
- Standard roles are `user` and `admin`.
- JWT secret key defaults to environment variable `JWT_SECRET_KEY`.
