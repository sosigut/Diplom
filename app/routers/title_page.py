import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.title_page import TitlePageRequest
from app.service.title_page_generator import generate_title_page_docx
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/title-page", tags=["title-page"])


@router.post("/generate")
def generate_title_page(
    data: TitlePageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    department = db.query(Department).filter(
        Department.id_department == current_user.id_department
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Кафедра пользователя не найдена")

    file_path = generate_title_page_docx(
        manual_title=data.manual_title,
        discipline_name=data.discipline_name,
        audience=data.audience,
        direction_code=data.direction_code,
        direction_name=data.direction_name,
        department_name=department.department_name,
        city=data.city,
        year=data.year,
        udk=data.udk,
        compiler_name=data.compiler_name,
        reviewer_name=data.reviewer_name,
        reviewer_degree=data.reviewer_degree,
        description=data.description,
    )

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )