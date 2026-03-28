from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id_refresh_token = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked = Column(Boolean, default=False, nullable=False)

    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(100), nullable=True)

    id_user = Column(Integer, ForeignKey("users.id_user", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")