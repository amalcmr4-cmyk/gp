# Password Reset Flow Implementation Guide

## Overview
This implementation provides a secure forgot-password and reset-password flow for your FastAPI application. The flow includes email verification, token generation with expiry, password strength validation, and secure password hashing.

## Architecture

### Backend Components

#### 1. Database Model Changes (`app/models/user.py`)
- **reset_token**: Unique token for password reset (URL-safe, 32 bytes)
- **reset_token_expiry**: Timestamp when reset token expires (default: 60 minutes)

#### 2. JWT Handler Functions (`app/auth/jwt_handler.py`)
- **generate_reset_token()**: Creates a cryptographically secure random token using `secrets.token_urlsafe(32)`
- **get_reset_token_expiry()**: Returns expiry datetime (current time + RESET_TOKEN_EXPIRE_MINUTES)

#### 3. API Endpoints (`app/routes/auth.py`)

##### POST /auth/forgot-password
**Request:**
```json
{
    "email": "user@example.com"
}
```

**Response:**
```json
{
    "detail": "If your email is registered, you will receive a password reset link shortly."
}
```

**Security Features:**
- Returns generic message regardless of email existence (prevents email enumeration)
- Generates reset token only if email exists
- Token stored in database with expiry time
- **TODO: Implement email sending** (see Email Integration section)

##### POST /auth/reset-password
**Request:**
```json
{
    "token": "reset_token_from_email",
    "new_password": "NewSecurePassword123!"
}
```

**Response:**
```json
{
    "detail": "Password reset successfully."
}
```

**Security Features:**
- Validates token exists and belongs to a user
- Checks token hasn't expired
- Validates new password meets strength requirements
- Hashes password with bcrypt before saving
- Clears reset token after successful reset
- Returns generic error messages (no info leakage)

### Frontend Components

#### forgot-password.html
- Simple email form
- Loading indicator
- Success/error alerts
- Redirects to login on success (3 second delay)

#### reset-password.html
- Extracts reset token from URL query parameter (`?token=...`)
- Password and confirm password fields
- Real-time password requirement validation:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
- Show/hide password toggle
- Validates password match
- Shows success alert and redirects to login

## Security Considerations

### ✓ Implemented
1. **Timing Attack Prevention**: Uses bcrypt for password verification
2. **Email Enumeration Prevention**: Generic success message in forgot-password
3. **Token Expiry**: Tokens expire after 60 minutes (configurable)
4. **Token Invalidation**: Reset token cleared after use
5. **Password Strength**: Enforced via Pydantic validators
6. **Secure Token Generation**: Uses `secrets.token_urlsafe()` instead of random
7. **No Error Details Leaked**: Generic error messages to frontend
8. **Bcrypt Hashing**: All passwords hashed with bcrypt before storage
9. **SQL Injection Protection**: Uses SQLAlchemy ORM
10. **HTTPS Recommended**: Add SSL/TLS in production

### ⚠️ TODO: Production Requirements

#### Email Integration
The current implementation logs reset tokens to console for debugging. In production, you must:

**Option 1: SendGrid**
```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_password_reset_email(email: str, reset_token: str):
    message = Mail(
        from_email="noreply@yourapp.com",
        to_emails=email,
        subject="Password Reset Request",
        html_content=f"""
            <h2>Password Reset Request</h2>
            <p>Click the link below to reset your password (valid for 1 hour):</p>
            <a href="https://yourapp.com/reset-password.html?token={reset_token}">
                Reset Password
            </a>
        """
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        sg.send(message)
    except Exception as e:
        print(f"Error sending email: {e}")
```

**Option 2: SMTP (Gmail, Outlook, etc.)**
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_password_reset_email(email: str, reset_token: str):
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Password Reset Request"
    message["From"] = sender_email
    message["To"] = email
    
    html = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Click the link below to reset your password (valid for 1 hour):</p>
                <a href="https://yourapp.com/reset-password.html?token={reset_token}">
                    Reset Password
                </a>
            </body>
        </html>
    """
    part = MIMEText(html, "html")
    message.attach(part)
    
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")
```

**Option 3: AWS SES**
```python
import boto3
from botocore.exceptions import ClientError

def send_password_reset_email(email: str, reset_token: str):
    ses_client = boto3.client('ses', region_name='us-east-1')
    
    try:
        response = ses_client.send_email(
            Source='noreply@yourapp.com',
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': 'Password Reset Request'},
                'Body': {'Html': {
                    'Data': f"""
                        <h2>Password Reset Request</h2>
                        <p>Click the link below to reset your password (valid for 1 hour):</p>
                        <a href="https://yourapp.com/reset-password.html?token={reset_token}">
                            Reset Password
                        </a>
                    """
                }}
            }
        )
    except ClientError as e:
        print(f"Error sending email: {e}")
```

#### Environment Variables (.env)
```env
# Password Reset
RESET_TOKEN_EXPIRE_MINUTES=60

# Email Configuration (example with Gmail)
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password

# Or SendGrid
SENDGRID_API_KEY=your-sendgrid-key

# Or AWS SES
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

#### Database Migration (if using Alembic)
```bash
alembic revision --autogenerate -m "Add reset token fields to User model"
alembic upgrade head
```

## Testing the Flow

### 1. Manual Testing

**Via Swagger UI:**
1. Go to `http://127.0.0.1:8000/docs`
2. Register a new account
3. Click "Try it out" on `/auth/forgot-password`
4. Enter registered email
5. Check console for reset token (or email inbox in production)
6. Navigate to `http://127.0.0.1:8000/reset-password.html?token=YOUR_TOKEN`
7. Enter new password
8. Login with new password

### 2. Python Test Script
```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# 1. Register
response = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "test@example.com",
    "password": "TestPassword123"
})
print("Register:", response.json())

# 2. Forgot Password
response = requests.post(f"{BASE_URL}/auth/forgot-password", json={
    "email": "test@example.com"
})
print("Forgot Password:", response.json())

# 3. Get reset token from database or console log
# In production, retrieve from email

# 4. Reset Password
response = requests.post(f"{BASE_URL}/auth/reset-password", json={
    "token": "YOUR_RESET_TOKEN",
    "new_password": "NewPassword456"
})
print("Reset Password:", response.json())

# 5. Login with new password
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "test@example.com",
    "password": "NewPassword456"
})
print("Login:", response.json())
```

## API Documentation

All endpoints are automatically documented in Swagger UI at `/docs`

### Error Handling

| Status | Scenario | Message |
|--------|----------|---------|
| 200 | Forgot-password successful | "If your email is registered..." |
| 200 | Reset-password successful | "Password reset successfully" |
| 400 | Invalid/expired token | "Invalid or expired password reset token" |
| 400 | Passwords don't match (frontend) | "Passwords do not match" |
| 400 | Weak password | Specific requirement not met |
| 500 | Server error | "An error occurred while resetting..." |

## Password Strength Requirements

All passwords must meet these requirements (enforced at both frontend and backend):
- ✓ Minimum 8 characters
- ✓ At least one uppercase letter (A-Z)
- ✓ At least one lowercase letter (a-z)
- ✓ At least one digit (0-9)

## Frontend URL Parameters

**Reset Password Page:**
- Query parameter: `?token=RESET_TOKEN`
- Example: `http://localhost:3000/reset-password.html?token=abc123def456`

## Database Schema Changes

```sql
-- SQLite migration
ALTER TABLE users ADD COLUMN reset_token VARCHAR UNIQUE;
ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME WITH TIMEZONE;

-- Index for faster lookups
CREATE INDEX idx_reset_token ON users(reset_token);
```

## Configuration Options

In `.env` file:
```env
# Token expiry time in minutes (default: 60)
RESET_TOKEN_EXPIRE_MINUTES=60

# Access token expiry (existing)
ACCESS_TOKEN_EXPIRE_MINUTES=60

# JWT Secret (existing)
JWT_SECRET_KEY=your-secret-key-here

# JWT Algorithm (existing)
JWT_ALGORITHM=HS256
```

## Common Issues & Solutions

### Issue: Reset token not working
**Solution:** Check token expiry time. Tokens expire after 60 minutes by default. Generate a new one.

### Issue: Email not sent
**Solution:** Implement email service as described in "Email Integration" section. Currently, tokens are logged to console.

### Issue: Password strength validation fails on frontend
**Solution:** Ensure password meets all 4 requirements shown in real-time validation UI.

### Issue: CORS errors
**Solution:** CORS is already configured in `main.py` to allow all origins. For production, restrict to specific domain:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Production Deployment Checklist

- [ ] Implement email sending (SendGrid, SMTP, or AWS SES)
- [ ] Set strong `JWT_SECRET_KEY` environment variable
- [ ] Configure `RESET_TOKEN_EXPIRE_MINUTES` appropriately
- [ ] Enable HTTPS/SSL on your server
- [ ] Restrict CORS origins to your frontend domain
- [ ] Test forgot-password → reset-password flow end-to-end
- [ ] Monitor email delivery success rate
- [ ] Set up error logging and monitoring
- [ ] Add rate limiting to prevent abuse (implement in future)
- [ ] Consider adding CAPTCHA to forgot-password form
- [ ] Review audit logs for security events

## Future Enhancements

1. **Rate Limiting**: Limit forgot-password requests per email/IP
2. **CAPTCHA**: Add Google reCAPTCHA to prevent bot abuse
3. **Email Verification**: Send verification code via email first
4. **SMS Option**: Allow password reset via SMS
5. **Password History**: Prevent reuse of last N passwords
6. **Audit Logging**: Log all password reset attempts
7. **Biometric Reset**: Support fingerprint/face recognition for reset
8. **WebAuthn**: Support FIDO2 security keys

## Support

For issues or questions, contact the development team.
