# Password Reset Flow - Visual Diagrams

## 1. Forgot Password Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USER FORGOT PASSWORD FLOW                        │
└─────────────────────────────────────────────────────────────────────┘

User Navigation:
┌────────────────────┐
│   Login Page       │
│  (login.html)      │
└────────┬───────────┘
         │ "Forgot Password?" link
         ▼
┌────────────────────────────┐
│  Forgot Password Page       │
│  (forgot-password.html)     │
│                            │
│  Input: Email address      │
└────────┬───────────────────┘
         │ Submit
         ▼
    ┌──────────────────────────────────────┐
    │ POST /auth/forgot-password           │
    │ Backend Processing                   │
    └──────────────────────────────────────┘
         │
         ├─ Email exists?
         │   ├─ YES → Generate token
         │   │        ├─ create_reset_token()
         │   │        ├─ get_reset_token_expiry()
         │   │        └─ Save to DB
         │   │            └─ user.reset_token
         │   │            └─ user.reset_token_expiry
         │   │
         │   └─ NO → Return generic message
         │            (security: prevent email enumeration)
         │
         ▼ Always return same message
    ┌──────────────────────────────────────┐
    │ Response 200 OK                      │
    │ "If email registered, link sent..."  │
    └──────────────────────────────────────┘
         │
         └─ In production: Send email with reset link
            - Email service (SendGrid/SMTP/SES)
            - Contains reset token in URL parameter
            - Valid for 60 minutes
            
         └─ In development: Log to console
            - Check: print(f"DEBUG: Reset token...")
```

## 2. Reset Password Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USER RESET PASSWORD FLOW                         │
└─────────────────────────────────────────────────────────────────────┘

User receives email with link:
└─ reset-password.html?token=XXXXXXXXXXXXX

User clicks link:
         │
         ▼
┌──────────────────────────────────────────┐
│  Reset Password Page                     │
│  (reset-password.html)                   │
│                                         │
│  • Extract token from URL query param   │
│  • Display password input form          │
│  • Show password strength requirements  │
│    - 8+ characters                      │
│    - 1+ uppercase                       │
│    - 1+ lowercase                       │
│    - 1+ digit                           │
└────────┬─────────────────────────────────┘
         │ Real-time validation shown
         │ User enters new password
         │ Submit
         ▼
    ┌──────────────────────────────────────────────┐
    │ POST /auth/reset-password                   │
    │ {                                           │
    │   "token": "XXXXX...",                      │
    │   "new_password": "NewPass123"              │
    │ }                                           │
    └──────────────────────────────────────────────┘
         │
         ├─ Validate token
         │   ├─ Token exists? ✓
         │   ├─ Token not expired? ✓
         │   └─ User found?
         │
         ├─ Validate password
         │   ├─ 8+ chars? ✓
         │   ├─ Uppercase? ✓
         │   ├─ Lowercase? ✓
         │   └─ Digit? ✓
         │
         ├─ Hash password (bcrypt)
         │
         ├─ Update database
         │   ├─ user.hashed_password = hash(new_password)
         │   ├─ user.reset_token = NULL
         │   └─ user.reset_token_expiry = NULL
         │
         └─ Commit transaction
         
         ▼
    ┌──────────────────────────────────────────────┐
    │ Response 200 OK                             │
    │ "Password reset successfully"               │
    └──────────────────────────────────────────────┘
         │
         ▼
    ┌──────────────────────────────────────────────┐
    │  Show success message (2 seconds)           │
    │  Redirect to Login Page                     │
    └──────────────────────────────────────────────┘
         │
         ▼
    ┌──────────────────────────────────────────────┐
    │  User logs in with new password             │
    │  POST /auth/login                           │
    │  Access granted ✓                           │
    └──────────────────────────────────────────────┘
```

## 3. Error Scenarios

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING FLOW                              │
└─────────────────────────────────────────────────────────────────────┘

Scenario 1: Invalid Token
    POST /auth/reset-password
    {token: "invalid_token", ...}
         │
         ├─ Query DB: SELECT * FROM users WHERE reset_token = ?
         │           → Result: NULL
         │
         ▼
    Response 400 Bad Request
    "Invalid or expired password reset token"
    (Generic message - no info leak)


Scenario 2: Token Expired
    POST /auth/reset-password
    {token: "valid_but_expired", ...}
         │
         ├─ Token found ✓
         ├─ Check expiry: NOW > token.reset_token_expiry
         │              → TRUE (expired)
         │
         ├─ Clear token: 
         │   ├─ user.reset_token = NULL
         │   └─ user.reset_token_expiry = NULL
         │   └─ Commit
         │
         ▼
    Response 400 Bad Request
    "Invalid or expired password reset token"
    (User must request new reset)


Scenario 3: Weak Password
    POST /auth/reset-password
    {token: "valid", new_password: "weak"}
         │
         ├─ Token validation ✓
         ├─ Password validation:
         │   ├─ Length >= 8? ✗ (only 4 chars)
         │   ├─ Return error
         │
         ▼
    Response 400/422 Validation Error
    "Password must be at least 8 characters long"


Scenario 4: Email Not Registered
    POST /auth/forgot-password
    {email: "notregistered@example.com"}
         │
         ├─ Query DB: SELECT * FROM users WHERE email = ?
         │           → Result: NULL
         │
         ├─ Skip token generation
         ├─ Return generic message anyway
         │   (Security feature!)
         │
         ▼
    Response 200 OK
    "If your email is registered, you will receive..."
    (Attacker can't enumerate emails)
```

## 4. Database State Changes

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DATABASE STATE TRANSITIONS                       │
└─────────────────────────────────────────────────────────────────────┘

Initial State (User Registered):
┌────────────────────────────────────────────┐
│ users table                                │
├────────────────────────────────────────────┤
│ id  │ email           │ hashed_pass... │ reset_token │ reset_expiry
├─────┼─────────────────┼────────────────┼─────────────┼──────────────
│  1  │ user@email.com  │ $2b$12$abc...  │    NULL     │    NULL
└────────────────────────────────────────────┘


After Forgot Password:
POST /auth/forgot-password {"email": "user@email.com"}
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ users table                                                │
├────────────────────────────────────────────────────────────┤
│ id  │ email           │ hashed_pass... │ reset_token    │ reset_expiry
├─────┼─────────────────┼────────────────┼────────────────┼──────────────
│  1  │ user@email.com  │ $2b$12$abc...  │ aBcD1f2g3h4... │ 2024-05-15
│     │                 │                │ (32 bytes)     │ 15:30 UTC
└────────────────────────────────────────────────────────────┘


After Reset Password:
POST /auth/reset-password {token: "aBcD1f2g3h4...", new_pass: "NewPass123"}
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ users table                                                │
├────────────────────────────────────────────────────────────┤
│ id  │ email           │ hashed_pass... │ reset_token │ reset_expiry
├─────┼─────────────────┼────────────────┼─────────────┼──────────────
│  1  │ user@email.com  │ $2b$12$xyz...  │    NULL     │    NULL
│     │                 │ (NEW hash)     │ (cleared)   │ (cleared)
└────────────────────────────────────────────────────────────┘
```

## 5. Security Layers Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                                  │
└─────────────────────────────────────────────────────────────────────┘

Layer 1: Email Level
    ├─ Email address enumeration prevention
    │  └─ Always return same message (can't tell if email exists)
    │
    └─ Email verification (production)
       └─ Only registered emails receive reset link


Layer 2: Token Level
    ├─ Secure generation
    │  └─ secrets.token_urlsafe(32) not random()
    │
    ├─ Token expiry
    │  └─ Expires after 60 minutes (configurable)
    │
    ├─ One-time use
    │  └─ Token cleared after password reset
    │
    └─ Storage
       └─ Stored in database with expiry timestamp


Layer 3: Password Level
    ├─ Strength requirements
    │  └─ 8+ chars, uppercase, lowercase, digit
    │
    ├─ Hashing
    │  └─ Bcrypt with per-password salt
    │
    └─ Validation
       └─ Enforced at both frontend and backend


Layer 4: Network Level
    ├─ HTTPS/SSL (required in production)
    │  └─ Token transmitted over encrypted connection
    │
    ├─ CORS configuration
    │  └─ Restrict to known origins
    │
    └─ Rate limiting (future)
       └─ Prevent brute force attempts


Layer 5: Error Handling
    ├─ Generic error messages
    │  └─ No internal details leaked
    │
    ├─ No email info disclosure
    │  └─ Same response for valid/invalid emails
    │
    └─ Logging
       └─ Log attempts for security monitoring
```

## 6. Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPONENT INTERACTIONS                           │
└─────────────────────────────────────────────────────────────────────┘

Frontend                Backend                Database              Email Service
    │                       │                       │                      │
    │ 1. Submit form       │                       │                      │
    ├──────────────────────>│                       │                      │
    │                       │ 2. Query user        │                      │
    │                       ├──────────────────────>│                      │
    │                       │<──────────────────────┤                      │
    │                       │ 3. Generate token    │                      │
    │                       │ 4. Save token & exp  │                      │
    │                       ├──────────────────────>│                      │
    │                       │<──────────────────────┤                      │
    │                       │ 5. Send email        │                      │
    │                       ├──────────────────────────────────────────────>│
    │                       │                      │                      │
    │ 6. Generic response  │                       │                      │
    │<──────────────────────┤                       │                      │
    │                       │                      │                      │
    │ 7. User clicks email link                    │                      │
    │    ?token=XXXXX      │                       │                      │
    │                       │                      │                      │
    │ 8. Reset password    │                       │                      │
    ├──────────────────────>│                       │                      │
    │                       │ 9. Validate token   │                      │
    │                       │ 10. Check expiry     │                      │
    │                       │ 11. Hash password    │                      │
    │                       │ 12. Update DB       │                      │
    │                       ├──────────────────────>│                      │
    │                       │<──────────────────────┤                      │
    │                       │ 13. Clear token     │                      │
    │                       ├──────────────────────>│                      │
    │                       │<──────────────────────┤                      │
    │ 14. Success response │                       │                      │
    │<──────────────────────┤                       │                      │
    │                       │                      │                      │
    │ 15. Redirect to login│                       │                      │
    │                       │                      │                      │
```

---

## Key Files Relationship

```
Backend:
  ├─ app/models/user.py
  │  └─ User model with reset_token, reset_token_expiry
  │
  ├─ app/auth/jwt_handler.py
  │  ├─ generate_reset_token()
  │  ├─ get_reset_token_expiry()
  │  └─ hash_password(), verify_password()
  │
  ├─ app/schemas/user_schema.py
  │  ├─ ForgotPasswordRequest
  │  └─ ResetPasswordRequest
  │
  └─ app/routes/auth.py
     ├─ POST /auth/forgot-password
     └─ POST /auth/reset-password

Frontend:
  ├─ login.html
  │  └─ Links to forgot-password.html
  │
  ├─ forgot-password.html
  │  ├─ Form: email input
  │  ├─ Calls: POST /auth/forgot-password
  │  └─ Shows: success/error alerts
  │
  ├─ reset-password.html
  │  ├─ Gets: ?token=XXX from URL
  │  ├─ Form: password input
  │  ├─ Calls: POST /auth/reset-password
  │  └─ Shows: password strength validation
  │
  ├─ forgot-password.css
  └─ reset-password.css

Testing:
  └─ test_password_reset.py
     └─ 9 test cases covering all scenarios

Documentation:
  ├─ PASSWORD_RESET_IMPLEMENTATION.md
  ├─ QUICK_REFERENCE.md
  └─ PASSWORD_RESET_FLOW_DIAGRAMS.md (this file)
```
