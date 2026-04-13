from sqlalchemy import Column, Integer, String, UniqueConstraint, DateTime, func

from app.db.base import Base


class Manual(Base):
    __tablename__ = "manual"

    id_manual = Column(Integer, primary_key=True, index=True)
    manual_name = Column(String(255), nullable=False)
    fio_user = Column(String(255), nullable=False)
    department_code = Column(Integer, nullable=False)
    faculty_code = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("file_hash", name="manual_file_hash_unique"),
    )