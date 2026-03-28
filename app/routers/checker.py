import hashlib
import os
import shutil
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.manual import Manual
from app.models.user import User
from app.service.checker import WordMethodicalChecker
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/checker", tags=["checker"])


def calculate_file_hash(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


@router.get("/ping")
def ping():
    return {"message": "checker router works"}


@router.post("/check")
async def check_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")

    if not file.filename.lower().endswith((".doc", ".docx")):
        raise HTTPException(status_code=400, detail="Поддерживаются только .doc и .docx")

    faculty = db.query(Faculty).filter(Faculty.id_faculty == current_user.id_faculty).first()
    department = db.query(Department).filter(Department.id_department == current_user.id_department).first()

    if not faculty or not department:
        raise HTTPException(status_code=404, detail="Не найден факультет или кафедра пользователя")

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_hash = calculate_file_hash(temp_path)

        existing_manual = db.query(Manual).filter(Manual.file_hash == file_hash).first()

        # Проверка выполняется ВСЕГДА, даже если запись уже есть
        with WordMethodicalChecker(visible=False, mark_document=True) as checker:
            report, checked_path = checker.check(temp_path)

        if not checked_path or not os.path.exists(checked_path):
            raise HTTPException(status_code=500, detail="Проверенный файл не был создан")

        # Если записи ещё нет — создаём
        if not existing_manual:
            manual = Manual(
                manual_name=file.filename,
                fio_user=current_user.fio,
                department_code=department.department_code,
                faculty_code=faculty.faculty_code,
                file_hash=file_hash,
            )
            db.add(manual)
            db.commit()
            db.refresh(manual)
        else:
            manual = existing_manual

        ext = os.path.splitext(checked_path)[1].lower()
        media_type = (
            "application/msword"
            if ext == ".doc"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        return FileResponse(
            path=checked_path,
            filename=os.path.basename(checked_path),
            media_type=media_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проверки документа: {str(e)}")
    finally:
        file.file.close()