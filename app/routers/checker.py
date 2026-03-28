import os
import shutil
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.manual import Manual
from app.models.user import User
from app.service.checker import WordMethodicalChecker
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/checker", tags=["checker"])


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

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with WordMethodicalChecker(visible=False, mark_document=True) as checker:
            report, checked_path = checker.check(temp_path)

        if not checked_path or not os.path.exists(checked_path):
            raise HTTPException(status_code=500, detail="Проверенный файл не был создан")

        manual = Manual(
            manual_name=file.filename,
            id_user=current_user.id_user,
            id_department=current_user.id_department,
            id_faculty=current_user.id_faculty,
        )
        db.add(manual)
        db.commit()
        db.refresh(manual)

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

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проверки документа: {str(e)}")

    finally:
        file.file.close()