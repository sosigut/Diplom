import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.title_page import TitlePageRequest, TutorialTitlePageRequest, MonographTitlePageRequest
from app.service.title_page_generator import (
    generate_title_page_docx,
    generate_tutorial_title_page_docx,
    generate_monograph_title_page_docx,
)
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
        reviewers=data.reviewers,
        description=data.description,
    )

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/generate-tutorial")
def generate_tutorial_title_page(
    data: TutorialTitlePageRequest,
    current_user: User = Depends(get_current_user),
):
    file_path = generate_tutorial_title_page_docx(
        author_name=data.author_name,
        tutorial_title=data.tutorial_title,
        city=data.city,
        year=data.year,
        reviewers=data.reviewers,
        a_value=data.a_value,
        isbn=data.isbn,
        directions=data.directions,
        udk=data.udk,
        bbk=data.bbk,
        description=data.description,
    )

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

@router.post("/generate-monograph")
def generate_monograph_title_page(
    data: MonographTitlePageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Генерация титульного листа монографии
    """
    file_path = generate_monograph_title_page_docx(
        authors=data.authors,
        monograph_title=data.monograph_title,
        city=data.city,
        year=data.year,
        udk=data.udk,
        bbk=data.bbk,
        isbn=data.isbn,
        description=data.description,
    )

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )