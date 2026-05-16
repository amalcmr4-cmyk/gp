from typing import Optional
import os
import smtplib
from email.mime.text import MIMEText

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.auth.dependencies import get_current_user, oauth2_scheme
from app.auth.jwt_handler import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    invalidate_refresh_token,
    is_refresh_token_valid,
    verify_password,
    hash_password,
    generate_reset_token,
    get_reset_token_expiry,
)
from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import (
    MessageResponse,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    #security Hash passwords with bcrypt before saving to the database.
    hashed_password = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    return new_user


@router.post("/login", response_model=TokenResponse)
def login_user(login: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == login.email).first()
    if user is None or not verify_password(login.password, user.hashed_password):
        #security Do not reveal whether the email or password was incorrect.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(refresh: TokenRefresh) -> TokenResponse:
    try:
        payload = decode_token(refresh.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )

    refresh_jti = payload.get("jti")
    if not refresh_jti or not is_refresh_token_valid(refresh_jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked.",
        )

    user_id = int(payload.get("sub"))

    #security Issue a new refresh token and revoke the old one to reduce reuse risk.
    invalidate_refresh_token(refresh_jti)
    new_refresh_token = create_refresh_token(user_id)
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=new_refresh_token,
    )


@router.post("/logout", response_model=MessageResponse)
def logout_user(
    current_user: User = Depends(get_current_user),
    credentials=Depends(oauth2_scheme),
    refresh: Optional[TokenRefresh] = Body(None),
) -> MessageResponse:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )

    jti = payload.get("jti")
    if jti:
        blacklist_token(jti)

    if refresh and refresh.refresh_token:
        try:
            refresh_payload = decode_token(refresh.refresh_token)
            if refresh_payload.get("type") == "refresh":
                invalidate_refresh_token(refresh_payload.get("jti"))
        except Exception:
            pass

    return MessageResponse(detail="Logout successful.")


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    """
    Request a password reset token.
    
    - **email**: User's email address
    
    Returns a generic success message for security (never reveals if email exists).
    If email is registered, a reset token is generated and stored in database.
    """
    #security Do not reveal if the email exists in the database to prevent email enumeration attacks
    user = db.query(User).filter(User.email == request.email).first()
    
    if user:
        #security Generate a secure reset token and set expiry time
        reset_token = generate_reset_token()
        reset_token_expiry = get_reset_token_expiry()
        
        user.reset_token = reset_token
        user.reset_token_expiry = reset_token_expiry
        db.commit()

        try:
            email_host = os.getenv("EMAIL_HOST")
            email_port = int(os.getenv("EMAIL_PORT", "0"))
            email_user = os.getenv("EMAIL_USER")
            email_password = os.getenv("EMAIL_PASSWORD")
            frontend_url = os.getenv("FRONTEND_URL", "").rstrip("/")

            if not email_host or not email_port or not email_user or not email_password or not frontend_url:
                raise ValueError("Incomplete SMTP configuration for password reset email.")

            reset_link = f"{frontend_url}/reset-password?token={reset_token}"
            email_body = (
                f"You requested a password reset.\n\n"
                f"Click the link below to reset your password:\n"
                f"{reset_link}\n\n"
                f"If you did not request this, please ignore this email."
            )

            message = MIMEText(email_body, "plain", "utf-8")
            message["Subject"] = "Password Reset Request"
            message["From"] = email_user
            message["To"] = user.email

            if email_port == 465:
                server = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
            else:
                server = smtplib.SMTP(email_host, email_port, timeout=10)
                server.starttls()

            try:
                server.login(email_user, email_password)
                server.sendmail(email_user, [user.email], message.as_string())
            finally:
                server.quit()
        except Exception as err:
            print(f"Password reset email failed for {request.email}: {err}")
    
    #security Always return the same message to prevent email enumeration
    return MessageResponse(
        detail="If your email is registered, you will receive a password reset link shortly."
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    """
    Reset password using a valid reset token.
    
    - **token**: Password reset token (received via email)
    - **new_password**: New password (must meet strength requirements)
    
    Validates token expiry before updating the password.
    """
    try:
        #security Query user by reset token
        user = db.query(User).filter(User.reset_token == request.token).first()
        
        if not user:
            #security Do not reveal if token was invalid or expired
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token.",
            )
        
        #security Check if reset token has expired
        if user.reset_token_expiry is None or datetime.now(timezone.utc) > user.reset_token_expiry.replace(tzinfo=timezone.utc):
            #security Clear the expired token
            user.reset_token = None
            user.reset_token_expiry = None
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token.",
            )
        
        #security Hash the new password with bcrypt
        hashed_password = hash_password(request.new_password)
        
        #security Update password and clear reset token
        user.hashed_password = hashed_password
        user.reset_token = None
        user.reset_token_expiry = None
        db.commit()
        
        return MessageResponse(detail="Password reset successfully.")
    
    except HTTPException:
        raise
    except Exception:
        #security Never expose internal database or server errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting your password.",
        )
