import os
import uuid
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import bcrypt
import jwt
from dotenv import load_dotenv

#security Load secret configuration from environment variables, not hard-coded values
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-secret-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
#security Password reset tokens expire in 1 hour by default
RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "60"))
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

#security In-memory token stores are acceptable for development, but production should use a persistent store.
ACCESS_TOKEN_BLACKLIST = set()
VALID_REFRESH_TOKENS = set()


def hash_password(password: str) -> str:
    #security Use bcrypt to hash passwords with a per-password salt, never store plain text.
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    #security Verify password using bcrypt to avoid timing attacks based on string comparison.
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def _create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.utcnow()
    jti = str(uuid.uuid4())
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta,
        "jti": jti,
        "type": token_type,
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def create_access_token(user_id: int) -> str:
    return _create_token(
        subject=str(user_id),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type=ACCESS_TOKEN_TYPE,
    )


def create_refresh_token(user_id: int) -> str:
    refresh_token = _create_token(
        subject=str(user_id),
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        token_type=REFRESH_TOKEN_TYPE,
    )
    payload = decode_token(refresh_token)
    VALID_REFRESH_TOKENS.add(payload["jti"])
    return refresh_token


def generate_reset_token() -> str:
    #security Generate a cryptographically secure random token for password reset
    return secrets.token_urlsafe(32)


def get_reset_token_expiry() -> datetime:
    #security Reset tokens expire after RESET_TOKEN_EXPIRE_MINUTES
    return datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)


def decode_token(token: str) -> Dict[str, Any]:
    #security Decode JWT tokens using a secret key and an explicit algorithm list.
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def blacklist_token(jti: str) -> None:
    ACCESS_TOKEN_BLACKLIST.add(jti)


def is_token_blacklisted(jti: str) -> bool:
    return jti in ACCESS_TOKEN_BLACKLIST


def is_refresh_token_valid(jti: str) -> bool:
    return jti in VALID_REFRESH_TOKENS


def invalidate_refresh_token(jti: str) -> None:
    VALID_REFRESH_TOKENS.discard(jti)
