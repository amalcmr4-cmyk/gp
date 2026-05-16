from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    #security Password reset token and expiry for secure password recovery flow
    reset_token = Column(String, nullable=True, unique=True)
    reset_token_expiry = Column(DateTime(timezone=True), nullable=True)
