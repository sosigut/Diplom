import hashlib
import os
import shutil
import tempfile
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Department, Faculty
from app.models.user import User
from app.service.checker import WordMethodicalChecker
from app.service.pdf_report import generate_error_report_pdf
from app.utils.dependencies import get_current_user
from app.models.manual import Manual
from app.models.tutorial import Tutorial
from app.models.monograph import Monograph

router = APIRouter(prefix="/checker", tags=["checker"])

BASE_DIR = os.getcwd()
CHECKED_DIR = os.path.join(BASE_DIR, "checked_files")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(CHECKED_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def calculate_file_hash(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


@router.get("/ping")
def ping():
    return {"message": "checker router works"}


@router.get("/download-checked/{filename}")
def download_checked_file(filename: str):
    file_path = os.path.join(CHECKED_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")

    ext = os.path.splitext(file_path)[1].lower()
    media_type = (
        "application/msword"
        if ext == ".doc"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
    )


@router.get("/report/{filename}")
def open_pdf_report(filename: str):
    file_path = os.path.join(REPORTS_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF-отчёт не найден")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
    )


@router.post("/check")
async def check_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")

    if not file.filename.lower().endswith((".doc", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только файлы формата .doc и .docx",
        )

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with WordMethodicalChecker(visible=False, mark_document=True) as checker:
            report, checked_path = checker.check(temp_path)

        if not checked_path or not os.path.exists(checked_path):
            raise HTTPException(status_code=500, detail="Не удалось создать проверенный файл")

        unique_id = uuid4().hex
        checked_filename = f"{unique_id}_{os.path.basename(checked_path)}"
        saved_checked_path = os.path.join(CHECKED_DIR, checked_filename)
        shutil.copy2(checked_path, saved_checked_path)

        has_problems = len(report.issues) > 0
        pdf_report_url = None

        if has_problems:
            pdf_filename = f"{unique_id}_report.pdf"
            pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

            generate_error_report_pdf(
                report=report,
                source_filename=file.filename,
                output_path=pdf_path,
            )

            pdf_report_url = str(request.url_for("open_pdf_report", filename=pdf_filename))
        else:
            file_hash = calculate_file_hash(temp_path)
            existing_manual = db.query(Manual).filter(Manual.file_hash == file_hash).first()

            if not existing_manual:
                department = db.query(Department).filter(Department.id_department == current_user.id_department).first()
                faculty = db.query(Faculty).filter(Faculty.id_faculty == current_user.id_faculty).first()

                manual = Manual(
                    manual_name=file.filename,
                    fio_user=current_user.fio,
                    faculty_code=faculty.faculty_code if faculty else "",
                    department_name=department.department_name if department else "",
                    file_hash=file_hash,
                )
                db.add(manual)
                db.commit()

        checked_file_url = str(
            request.url_for("download_checked_file", filename=checked_filename)
        )

        return {
            "message": "Проверка завершена",
            "has_errors": has_problems,
            "errors_count": len(report.issues),
            "warnings_count": 0,
            "checked_file_url": checked_file_url,
            "pdf_report_url": pdf_report_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проверки документа: {str(e)}")
    finally:
        try:
            file.file.close()
        except Exception:
            pass
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("/my/{doc_type}")
def get_my_documents(
        doc_type: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    """
    Получение списка документов текущего пользователя по типу
    doc_type: manual, tutorial, monograph
    """
    if doc_type == "manual":
        documents = db.query(Manual).filter(
            Manual.fio_user == current_user.fio
        ).order_by(Manual.created_at.desc()).all()

        return [
            {
                "id": d.id_manual,
                "name": d.manual_name,
                "fio_user": d.fio_user,
                "faculty_code": d.faculty_code,
                "department_name": d.department_name,
                "created_at": d.created_at,
                "type": "manual"
            }
            for d in documents
        ]

    elif doc_type == "tutorial":
        documents = db.query(Tutorial).filter(
            Tutorial.fio_user == current_user.fio
        ).order_by(Tutorial.created_at.desc()).all()

        return [
            {
                "id": d.id_tutorial,
                "name": d.tutorial_name,
                "fio_user": d.fio_user,
                "faculty_code": d.faculty_code,
                "department_name": d.department_name,
                "created_at": d.created_at,
                "type": "tutorial"
            }
            for d in documents
        ]

    elif doc_type == "monograph":
        documents = db.query(Monograph).filter(
            Monograph.fio_user == current_user.fio
        ).order_by(Monograph.created_at.desc()).all()

        return [
            {
                "id": d.id_monograph,
                "name": d.monograph_name,
                "fio_user": d.fio_user,
                "faculty_code": d.faculty_code,
                "department_name": d.department_name,
                "created_at": d.created_at,
                "type": "monograph"
            }
            for d in documents
        ]

    else:
        raise HTTPException(status_code=400, detail="Неверный тип документа")


@router.post("/check")
async def check_document(
        request: Request,
        file: UploadFile = File(...),
        doc_type: str = Form(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")

    if not file.filename.lower().endswith((".doc", ".docx")):
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только файлы формата .doc и .docx",
        )

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with WordMethodicalChecker(visible=False, mark_document=True) as checker:
            report, checked_path = checker.check(temp_path)

        if not checked_path or not os.path.exists(checked_path):
            raise HTTPException(status_code=500, detail="Не удалось создать проверенный файл")

        unique_id = uuid4().hex
        checked_filename = f"{unique_id}_{os.path.basename(checked_path)}"
        saved_checked_path = os.path.join(CHECKED_DIR, checked_filename)
        shutil.copy2(checked_path, saved_checked_path)

        has_problems = len(report.issues) > 0
        pdf_report_url = None

        if has_problems:
            pdf_filename = f"{unique_id}_report.pdf"
            pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

            generate_error_report_pdf(
                report=report,
                source_filename=file.filename,
                output_path=pdf_path,
            )

            pdf_report_url = str(request.url_for("open_pdf_report", filename=pdf_filename))
        else:
            file_hash = calculate_file_hash(temp_path)

            # Сохраняем в соответствующую таблицу в зависимости от типа документа
            department = db.query(Department).filter(Department.id_department == current_user.id_department).first()
            faculty = db.query(Faculty).filter(Faculty.id_faculty == current_user.id_faculty).first()

            if doc_type == "manual":
                existing = db.query(Manual).filter(Manual.file_hash == file_hash).first()
                if not existing:
                    document = Manual(
                        manual_name=file.filename,
                        fio_user=current_user.fio,
                        faculty_code=faculty.faculty_code if faculty else "",
                        department_name=department.department_name if department else "",
                        file_hash=file_hash,
                    )
                    db.add(document)
            elif doc_type == "tutorial":
                existing = db.query(Tutorial).filter(Tutorial.file_hash == file_hash).first()
                if not existing:
                    document = Tutorial(
                        tutorial_name=file.filename,
                        fio_user=current_user.fio,
                        faculty_code=faculty.faculty_code if faculty else "",
                        department_name=department.department_name if department else "",
                        file_hash=file_hash,
                    )
                    db.add(document)
            elif doc_type == "monograph":
                existing = db.query(Monograph).filter(Monograph.file_hash == file_hash).first()
                if not existing:
                    document = Monograph(
                        monograph_name=file.filename,
                        fio_user=current_user.fio,
                        faculty_code=faculty.faculty_code if faculty else "",
                        department_name=department.department_name if department else "",
                        file_hash=file_hash,
                    )
                    db.add(document)
            else:
                raise HTTPException(status_code=400, detail="Неверный тип документа")

            db.commit()

        checked_file_url = str(
            request.url_for("download_checked_file", filename=checked_filename)
        )

        return {
            "message": "Проверка завершена",
            "has_errors": has_problems,
            "errors_count": len(report.issues),
            "warnings_count": 0,
            "checked_file_url": checked_file_url,
            "pdf_report_url": pdf_report_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проверки документа: {str(e)}")
    finally:
        try:
            file.file.close()
        except Exception:
            pass
        shutil.rmtree(temp_dir, ignore_errors=True)