from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Monograph(Base):
    __tablename__ = "monographs"

    id_monograph = Column(Integer, primary_key=True, index=True)
    monograph_name = Column(String(255), nullable=False)
    fio_user = Column(String(255), nullable=False)
    faculty_code = Column(String(10), nullable=False)
    department_name = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)