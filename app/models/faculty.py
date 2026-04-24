from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Faculty(Base):
    __tablename__ = "faculty"

    id_faculty = Column(Integer, primary_key=True, index=True)
    faculty_name = Column(String(255), nullable=False)
    faculty_code = Column(String(10), unique=True, nullable=False)  # теперь строка вида __.__.__
    dean_fio = Column(String(255), nullable=False)
    manual_count = Column(Integer, default=0)

    departments = relationship("Department", back_populates="faculty", cascade="all, delete")
    users = relationship("User", back_populates="faculty")