from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.user import User
from app.schemas.auth import UserLogin, UserRegister
from app.schemas.token import MessageResponse, RefreshTokenRequest, TokenPair
from app.schemas.user import UserInfo
from app.service.auth_service import (
    login_user,
    logout_all_user_sessions,
    logout_user,
    refresh_user_token,
    register_user,
)
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserInfo)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    user = register_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        faculty_code=user_data.faculty_code,
        department_code=user_data.department_code,
        role=user_data.role,
    )

    faculty = db.query(Faculty).filter(Faculty.id_faculty == user.id_faculty).first()
    department = db.query(Department).filter(Department.id_department == user.id_department).first()

    return UserInfo(
        id_user=user.id_user,
        email=user.email,
        role=user.role,
        faculty_name=faculty.faculty_name if faculty else "",
        department_name=department.department_name if department else "",
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenPair)
def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    access_token, refresh_token = login_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        request=request,
    )

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenPair)
def refresh_tokens(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    new_access_token = refresh_user_token(db=db, refresh_token=data.refresh_token)

    return TokenPair(
        access_token=new_access_token,
        refresh_token=data.refresh_token,
        token_type="bearer",
    )


@router.post("/logout", response_model=MessageResponse)
def logout(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    logout_user(db=db, refresh_token=data.refresh_token)
    return MessageResponse(message="Выход выполнен успешно")


@router.post("/logout-all", response_model=MessageResponse)
def logout_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logout_all_user_sessions(db=db, user_id=current_user.id_user)
    return MessageResponse(message="Выход со всех устройств выполнен успешно")


@router.get("/me", response_model=UserInfo)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.id_faculty == current_user.id_faculty).first()
    department = db.query(Department).filter(Department.id_department == current_user.id_department).first()

    return UserInfo(
        id_user=current_user.id_user,
        email=current_user.email,
        role=current_user.role,
        faculty_name=faculty.faculty_name if faculty else "",
        department_name=department.department_name if department else "",
        created_at=current_user.created_at,
    )