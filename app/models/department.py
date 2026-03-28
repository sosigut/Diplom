from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Department(Base):
    __tablename__ = "department"

    id_department = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(255), nullable=False)
    department_code = Column(Integer, nullable=False, unique=True)
    manual_count = Column(Integer, default=0)

    id_faculty = Column(Integer, ForeignKey("faculty.id_faculty", ondelete="CASCADE"), nullable=False)

    faculty = relationship("Faculty", back_populates="departments")
    users = relationship("User", back_populates="department")
    manuals = relationship("Manual", back_populates="department")