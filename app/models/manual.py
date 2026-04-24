from sqlalchemy import Column, Integer, String, UniqueConstraint, DateTime, func

from app.db.base import Base


class Manual(Base):
    __tablename__ = "manual"

    id_manual = Column(Integer, primary_key=True, index=True)
    manual_name = Column(String(255), nullable=False)
    fio_user = Column(String(255), nullable=False)
    faculty_code = Column(String(10), nullable=False)  # теперь строка вида __.__.__
    department_name = Column(String(255), nullable=False)  # добавляем название кафедры
    file_hash = Column(String(64), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("file_hash", name="manual_file_hash_unique"),
    )