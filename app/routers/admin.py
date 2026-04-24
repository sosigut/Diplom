from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.faculty import Faculty
from app.schemas.admin import (
    DepartmentCreate,
    DepartmentResponse,
    FacultyCreate,
    FacultyResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/faculty", response_model=FacultyResponse, status_code=status.HTTP_201_CREATED)
def create_faculty(data: FacultyCreate, db: Session = Depends(get_db)):
    existing_faculty = db.query(Faculty).filter(
        (Faculty.faculty_code == data.faculty_code) |
        (Faculty.faculty_name == data.faculty_name)
    ).first()

    if existing_faculty:
        raise HTTPException(
            status_code=400,
            detail="Факультет с таким названием или кодом уже существует"
        )

    faculty = Faculty(
        faculty_name=data.faculty_name,
        faculty_code=data.faculty_code,
        dean_fio=data.dean_fio,
        manual_count=0
    )

    db.add(faculty)
    db.commit()
    db.refresh(faculty)

    return faculty


@router.post("/department", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.faculty_code == data.faculty_code).first()

    if not faculty:
        raise HTTPException(
            status_code=404,
            detail="Факультет с таким кодом не найден"
        )

    existing_department = db.query(Department).filter(
        Department.department_name == data.department_name
    ).first()

    if existing_department:
        raise HTTPException(
            status_code=400,
            detail="Кафедра с таким названием уже существует"
        )

    department = Department(
        department_name=data.department_name,
        manual_count=0,
        id_faculty=faculty.id_faculty
    )

    db.add(department)
    db.commit()
    db.refresh(department)

    return department