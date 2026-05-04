import os
import shutil
import tempfile
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.service.email import send_to_rio
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/rio", tags=["rio"])


class RioCommentRequest(BaseModel):
    comment: str


# Временное хранилище для файлов пользователей
temp_file_storage = {}


@router.post("/upload-step1")
async def upload_step1_files(
        files: List[UploadFile] = File(...),
        current_user: User = Depends(get_current_user)
):
    """Шаг 1: Загрузка двух любых файлов"""
    if len(files) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо загрузить ровно 2 файла"
        )

    allowed_extensions = {'.doc', '.docx', '.pdf', '.txt', '.rtf', '.odt'}

    uploaded_files = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Файл {file.filename} имеет неподдерживаемое расширение"
            )

        user_dir = os.path.join(tempfile.gettempdir(), f"rio_{current_user.id_user}")
        os.makedirs(user_dir, exist_ok=True)

        file_path = os.path.join(user_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        uploaded_files.append({
            "filename": file.filename,
            "path": file_path
        })

    if current_user.id_user not in temp_file_storage:
        temp_file_storage[current_user.id_user] = {}

    temp_file_storage[current_user.id_user]["step1_files"] = uploaded_files

    return JSONResponse(content={
        "success": True,
        "message": "Файлы успешно загружены",
        "files": [f["filename"] for f in uploaded_files],
        "next_step": 2
    })


@router.post("/upload-step2")
async def upload_step2_file(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user)
):
    """Шаг 2: Загрузка файла для проверки"""
    if current_user.id_user not in temp_file_storage or \
            "step1_files" not in temp_file_storage[current_user.id_user]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала загрузите файлы на шаге 1"
        )

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {'.doc', '.docx'}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только файлы .doc и .docx"
        )

    user_dir = os.path.join(tempfile.gettempdir(), f"rio_{current_user.id_user}")
    os.makedirs(user_dir, exist_ok=True)

    file_path = os.path.join(user_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Проверка файла через WordMethodicalChecker
    has_errors = await check_file_for_errors(file_path, file.filename)

    step2_file = {
        "filename": file.filename,
        "path": file_path,
        "has_errors": has_errors
    }

    temp_file_storage[current_user.id_user]["step2_file"] = step2_file

    if has_errors:
        return JSONResponse(content={
            "success": False,
            "message": f'В данном документе "{file.filename}" имеются ошибки, выполните полную проверку файла',
            "has_errors": True,
            "filename": file.filename
        }, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return JSONResponse(content={
        "success": True,
        "message": "Файл успешно проверен",
        "filename": file.filename,
        "next_step": 3
    })


async def check_file_for_errors(file_path: str, filename: str) -> bool:
    """Проверка файла на наличие ошибок"""
    try:
        from app.service.checker import WordMethodicalChecker

        with WordMethodicalChecker(visible=False, mark_document=False) as checker:
            report, _ = checker.check(file_path)
            return len(report.issues) > 0
    except Exception as e:
        print(f"Ошибка проверки файла {filename}: {e}")
        return True


@router.post("/submit-step3")
async def submit_step3(
        request: RioCommentRequest,
        current_user: User = Depends(get_current_user)
):
    """Шаг 3: Отправка всех файлов на email"""
    if current_user.id_user not in temp_file_storage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сессия не найдена. Начните процесс заново."
        )

    user_storage = temp_file_storage[current_user.id_user]

    if "step1_files" not in user_storage or "step2_file" not in user_storage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не все файлы загружены"
        )

    all_files = user_storage["step1_files"] + [user_storage["step2_file"]]
    file_paths = [f["path"] for f in all_files]
    file_names = [f["filename"] for f in all_files]

    if user_storage["step2_file"].get("has_errors", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл содержит ошибки. Исправьте их."
        )

    try:
        send_to_rio(
            user_fio=current_user.fio,
            user_email=current_user.email,
            comment=request.comment,
            file_paths=file_paths,
            file_names=file_names
        )

        # Очищаем временные файлы
        user_dir = os.path.dirname(file_paths[0])
        shutil.rmtree(user_dir, ignore_errors=True)
        del temp_file_storage[current_user.id_user]

        return JSONResponse(content={
            "success": True,
            "message": "Файлы успешно отправлены в РИО"
        })

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка отправки: {str(e)}"
        )


@router.post("/reset")
async def reset_session(current_user: User = Depends(get_current_user)):
    """Сброс сессии"""
    if current_user.id_user in temp_file_storage:
        user_storage = temp_file_storage[current_user.id_user]
        for key in user_storage:
            if key == "step1_files":
                for f in user_storage[key]:
                    if os.path.exists(f.get("path", "")):
                        os.remove(f.get("path", ""))
            elif isinstance(user_storage[key], dict) and "path" in user_storage[key]:
                if os.path.exists(user_storage[key]["path"]):
                    os.remove(user_storage[key]["path"])
        del temp_file_storage[current_user.id_user]

    return JSONResponse(content={
        "success": True,
        "message": "Сессия сброшена"
    })