# Requirements: User Authentication (JWT & Roles)

## Requirement 1: User Registration
When a user submits valid registration details (email, password, optional first name and last name), the Budget Checker backend shall create a new user account with hashed password and default role "user", and issue JWT access and refresh tokens.

### Rationale
Enables new users to securely register an account with role assignment.

### Verification
Post valid registration payload to `/api/v1/auth/register` and verify 201 response containing access_token, refresh_token, and user object with role "user".

### Traces to
[[concept-1]]

### Metadata
```json
{
  "pattern": "event-driven",
  "system": "Budget Checker backend",
  "trigger": "a user submits valid registration details",
  "response": "create a new user account with hashed password and default role user, and issue JWT access and refresh tokens",
  "traces_to": ["concept-1"]
}
```

## Requirement 2: User Authentication
When a user provides valid login credentials (email and password), the Budget Checker backend shall authenticate the user and return JWT access and refresh tokens.

### Rationale
Allows registered users to sign in and receive credentials for protected API endpoints.

### Verification
Post valid email and password to `/api/v1/auth/login` and verify 200 response with Bearer tokens.

### Traces to
[[concept-1]]

### Metadata
```json
{
  "pattern": "event-driven",
  "system": "Budget Checker backend",
  "trigger": "a user provides valid login credentials",
  "response": "authenticate the user and return JWT access and refresh tokens",
  "traces_to": ["concept-1"]
}
```

## Requirement 3: Invalid Credentials Handling
If a user submits invalid email or password credentials during login, then the Budget Checker backend shall return HTTP 401 Unauthorized status with error detail.

### Rationale
Prevents unauthorized access and informs the user of invalid authentication attempts.

### Verification
Post invalid password to `/api/v1/auth/login` and assert status 401 Unauthorized.

### Traces to
[[concept-1]]

### Metadata
```json
{
  "pattern": "unwanted-behaviour",
  "system": "Budget Checker backend",
  "trigger": "a user submits invalid email or password credentials during login",
  "response": "return HTTP 401 Unauthorized status with error detail",
  "traces_to": ["concept-1"]
}
```

## Requirement 4: Header User Dropdown UI
While a user is authenticated, the Budget Checker frontend header shall display a user profile icon with a dropdown showing full name, email, role badge, settings, and logout option.

### Rationale
Provides immediate visual context of authenticated state and account control.

### Verification
Sign in on the frontend and verify header renders user initial avatar and dropdown details.

### Traces to
[[concept-1]]

### Metadata
```json
{
  "pattern": "state-driven",
  "system": "Budget Checker frontend header",
  "precondition": "a user is authenticated",
  "response": "display a user profile icon with a dropdown showing full name, email, role badge, settings, and logout option",
  "traces_to": ["concept-1"]
}
```

## Requirement 5: Role-based Authorization Dependency
The Budget Checker backend shall enforce role requirements on protected endpoints using dependency injection.

### Rationale
Ensures administrative endpoints require "admin" role while standard endpoints accept active users.

### Verification
Invoke protected admin endpoint as standard user and verify HTTP 403 Forbidden.

### Traces to
[[concept-1]]

### Metadata
```json
{
  "pattern": "ubiquitous",
  "system": "Budget Checker backend",
  "response": "enforce role requirements on protected endpoints using dependency injection",
  "traces_to": ["concept-1"]
}
```
