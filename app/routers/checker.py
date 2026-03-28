import os
import shutil
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.service.checker import WordMethodicalChecker

router = APIRouter(prefix="/checker", tags=["checker"])


@router.get("/ping")
def ping():
    return {"message": "checker router works"}


@router.post("/check")
async def check_document(file: UploadFile = File(...)):
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

        return {
            "filename": file.filename,
            "summary": report.summary(),
            "issues": [
                {
                    "rule": issue.rule,
                    "severity": issue.severity,
                    "location": issue.location,
                    "message": issue.message,
                    "priority": issue.priority,
                }
                for issue in report.issues
            ],
            "checked_file_path": checked_path,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проверки документа: {str(e)}")

    finally:
        file.file.close()