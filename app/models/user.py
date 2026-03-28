from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id_user = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    id_faculty = Column(Integer, ForeignKey("faculty.id_faculty", ondelete="RESTRICT"), nullable=False)
    id_department = Column(Integer, ForeignKey("department.id_department", ondelete="RESTRICT"), nullable=False)

    faculty = relationship("Faculty", back_populates="users")
    department = relationship("Department", back_populates="users")
    manuals = relationship("Manual", back_populates="user", cascade="all, delete")

    __table_args__ = (
        CheckConstraint(
            "role IN ('Доцент', 'Профессор', 'Старший преподаватель', 'Преподаватель', 'Аспирант')",
            name="users_role_check"
        ),
    )