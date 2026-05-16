# Production Deployment Checklist

## Pre-Deployment ✓

### Testing Phase
- [ ] Run `python test_password_reset.py` - all 9 tests pass
- [ ] Manual test: Forgot password → Reset password → Login flow
- [ ] Test with valid and invalid tokens
- [ ] Test with weak passwords
- [ ] Test email enumeration prevention (non-existent email)
- [ ] Test token expiry (wait 61+ minutes)
- [ ] Test on different browsers (Chrome, Firefox, Safari, Edge)
- [ ] Test on mobile devices
- [ ] Verify Swagger UI documentation at `/docs`

### Database
- [ ] Database migration applied (alembic or manual SQL)
- [ ] Verify columns exist: `reset_token`, `reset_token_expiry`
- [ ] Run integrity check on database
- [ ] Backup production database before deploying

### Backend Configuration
- [ ] `JWT_SECRET_KEY` set to strong value (not default)
  ```env
  JWT_SECRET_KEY=your-very-long-random-string-here-min-32-chars
  ```
- [ ] `RESET_TOKEN_EXPIRE_MINUTES` set (default 60 min is reasonable)
- [ ] Email service credentials configured
  - [ ] `SENDGRID_API_KEY` OR
  - [ ] `SMTP_*` variables OR
  - [ ] `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- [ ] All environment variables in `.env` or deployment config
- [ ] `.env` file NOT committed to git

### Email Service Setup
- [ ] **SendGrid** (if chosen)
  - [ ] Account created at sendgrid.com
  - [ ] API key generated and stored in `.env`
  - [ ] Sender email verified
  - [ ] `pip install sendgrid`
  - [ ] Email template created
  
- [ ] **SMTP** (if chosen, e.g., Gmail)
  - [ ] SMTP credentials obtained
  - [ ] For Gmail: Enable "Less secure apps" OR use App Password
  - [ ] `pip install python-dotenv`
  - [ ] Test email sending manually
  
- [ ] **AWS SES** (if chosen)
  - [ ] AWS account and SES access configured
  - [ ] Sender email verified in SES
  - [ ] `pip install boto3`
  - [ ] IAM permissions set correctly

- [ ] Email implementation completed in `app/routes/auth.py`
  - [ ] Replace `print(f"DEBUG: Reset token...")` with email sending
  - [ ] Test email delivery end-to-end
  - [ ] Verify email includes reset link with token
  - [ ] Email template is clear and branded

### Frontend Configuration
- [ ] Update API base URL (if not localhost)
  ```javascript
  // forgot-password.html & reset-password.html
  const BASE_URL = "https://yourdomain.com/api";  // Not http://127.0.0.1:8000
  ```
- [ ] Verify forgot-password.html links to login
- [ ] Verify reset-password.html extracts token from URL correctly
- [ ] Test frontend on different screen sizes (responsive design)
- [ ] Verify CSS loads correctly (check browser dev tools)

### Security
- [ ] HTTPS/SSL enabled on server
- [ ] Update CORS configuration (restrict origins)
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://yourdomain.com"],  # Not ["*"]
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- [ ] Update frontend URLs from `http://` to `https://`
- [ ] Update API URLs in frontend from `http://127.0.0.1:8000` to `https://api.yourdomain.com`
- [ ] Verify password requirements are enforced (8 chars, upper, lower, digit)
- [ ] Verify generic error messages (no info leakage)
- [ ] Verify token is stored securely (database, not memory)

### Logging & Monitoring
- [ ] Error logging configured
- [ ] Remove or comment out `print(f"DEBUG: Reset token...")` before going live
- [ ] Add structured logging for password reset attempts
- [ ] Set up monitoring for:
  - [ ] Failed password reset attempts
  - [ ] Successful password resets
  - [ ] Email delivery failures
  - [ ] Database errors

### Documentation
- [ ] Update API documentation with new endpoints
- [ ] Update user-facing help docs with password reset flow
- [ ] Document email sending in deployment notes
- [ ] Document emergency recovery procedure (admin password reset)

---

## Deployment Phase

### Code Deployment
- [ ] All code changes committed and reviewed
- [ ] Tests passing in CI/CD pipeline
- [ ] Code deployed to staging environment first
- [ ] Staging environment tested end-to-end
- [ ] Code deployed to production
- [ ] Verify endpoints accessible: `/docs`, `/auth/forgot-password`, `/auth/reset-password`

### Database Deployment
- [ ] Database backup taken
- [ ] Migration applied (or columns added manually)
- [ ] Verify schema: `PRAGMA table_info(users);`
- [ ] Verify constraints are in place (UNIQUE on reset_token)

### Service Deployment
- [ ] FastAPI server running
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables loaded
- [ ] Email service tested (send test email)
- [ ] Database connection verified

---

## Post-Deployment ✓

### Functionality Verification
- [ ] Test forgot password flow end-to-end
- [ ] Verify email received with reset link
- [ ] Click link in email → reset password page loads
- [ ] Submit new password → success message shown
- [ ] Login with new password → works
- [ ] Verify token is cleared from database after reset
- [ ] Test with expired token (60+ minutes old)
- [ ] Test with invalid token
- [ ] Test non-existent email (verify generic message)

### Security Verification
- [ ] HTTPS/SSL working (no warnings)
- [ ] Email not leaked in error messages
- [ ] Tokens not exposed in logs
- [ ] CORS headers correct (check browser dev tools)
- [ ] CSP (Content Security Policy) headers set (if applicable)
- [ ] X-Frame-Options header set (if applicable)

### Performance
- [ ] Forgot password request < 1 second
- [ ] Reset password request < 1 second
- [ ] Email delivery within 5 minutes
- [ ] No database connection leaks
- [ ] Server logs show no errors

### Monitoring & Alerts
- [ ] Email delivery failures alert configured
- [ ] Database connection failures alert configured
- [ ] High number of reset attempts alert configured
- [ ] Error rate monitoring active
- [ ] Logs being collected (ELK, Datadog, CloudWatch, etc.)

### User Communication
- [ ] Announcement sent about password reset feature
- [ ] Help documentation updated
- [ ] Support team trained on feature
- [ ] FAQ updated with reset password procedures
- [ ] Status page updated (if applicable)

---

## Troubleshooting & Rollback

### If Email Not Sending
1. [ ] Check email service API key is correct
2. [ ] Verify sender email is verified in email service
3. [ ] Check network connectivity to email service
4. [ ] Review email service logs for delivery failures
5. [ ] Verify SMTP credentials if using SMTP
6. [ ] Check spam/junk folder in test email

### If Database Error
1. [ ] Verify database connection string
2. [ ] Check if migration was applied: `SELECT * FROM users LIMIT 1;`
3. [ ] Verify columns exist: `PRAGMA table_info(users);`
4. [ ] Check database permissions
5. [ ] Restore from backup if needed

### If Frontend Not Working
1. [ ] Verify API URLs in HTML files (not localhost)
2. [ ] Check browser console for JavaScript errors
3. [ ] Verify CSS files are loading (check Network tab)
4. [ ] Check CORS headers (Options tab)
5. [ ] Verify form submission is reaching backend

### Rollback Procedure
If critical issues:
1. [ ] Stop accepting new reset requests
2. [ ] Roll back code to previous version
3. [ ] Keep new database schema (migration)
4. [ ] Notify users of temporary unavailability
5. [ ] Restore service and test thoroughly

---

## Post-Launch Maintenance

### Weekly
- [ ] Review email delivery metrics
- [ ] Check error logs for issues
- [ ] Monitor password reset success rate

### Monthly
- [ ] Review security logs
- [ ] Update dependencies
- [ ] Test disaster recovery
- [ ] Review token expiry times (appropriate?)

### Quarterly
- [ ] Security audit
- [ ] Performance review
- [ ] User feedback collection
- [ ] Consider additional features (2FA, etc.)

### Annually
- [ ] Full security assessment
- [ ] Penetration testing
- [ ] Update documentation
- [ ] Review and update deployment procedures

---

## Additional Enhancements (Future)

- [ ] **Rate Limiting**: Limit forgot-password to 3 attempts per hour per IP
- [ ] **CAPTCHA**: Add Google reCAPTCHA to prevent bot abuse
- [ ] **2FA**: Require 2FA for reset-password confirmation
- [ ] **SMS**: Allow SMS delivery of reset codes
- [ ] **Audit Trail**: Log all password reset attempts
- [ ] **IP Whitelisting**: For admin accounts
- [ ] **Suspicious Activity Detection**: Alert on unusual patterns

---

## Sign-off

- [ ] Deployment lead approval
- [ ] Security team approval
- [ ] Database team approval
- [ ] DevOps approval
- [ ] Product owner sign-off

**Deployed by:** ________________  
**Date:** ________________  
**Version:** ________________  
**Environment:** □ Production  □ Staging  □ Development

---

## Deployment Notes

(Add any additional notes, issues encountered, or customizations made)

```
[Your deployment notes here]
```
