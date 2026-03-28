from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Manual(Base):
    __tablename__ = "manual"

    id_manual = Column(Integer, primary_key=True, index=True)
    manual_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    id_user = Column(Integer, ForeignKey("users.id_user", ondelete="CASCADE"), nullable=False)
    id_department = Column(Integer, ForeignKey("department.id_department", ondelete="RESTRICT"), nullable=False)
    id_faculty = Column(Integer, ForeignKey("faculty.id_faculty", ondelete="RESTRICT"), nullable=False)

    user = relationship("User", back_populates="manuals")
    department = relationship("Department", back_populates="manuals")
    faculty = relationship("Faculty", back_populates="manuals")