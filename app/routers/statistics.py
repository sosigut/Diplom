from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.manual import Manual
from app.models.tutorial import Tutorial
from app.models.monograph import Monograph
from app.models.user import User
from app.schemas.statistics import StatisticsResponse
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/statistics", tags=["statistics"])


def build_datetime_range(date_from: date, date_to: date):
    start_dt = datetime.combine(date_from, time.min)
    end_dt = datetime.combine(date_to, time.max)
    return start_dt, end_dt


@router.get("/faculty", response_model=StatisticsResponse)
def count_by_faculty(
    faculty_code: str = Query(..., pattern=r'^\d{2}\.\d{2}\.\d{2}$'),
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть больше date_to")

    start_dt, end_dt = build_datetime_range(date_from, date_to)

    manual_count = db.query(Manual).filter(
        Manual.faculty_code == faculty_code,
        Manual.created_at >= start_dt,
        Manual.created_at <= end_dt,
    ).count()

    tutorial_count = db.query(Tutorial).filter(
        Tutorial.faculty_code == faculty_code,
        Tutorial.created_at >= start_dt,
        Tutorial.created_at <= end_dt,
    ).count()

    monograph_count = db.query(Monograph).filter(
        Monograph.faculty_code == faculty_code,
        Monograph.created_at >= start_dt,
        Monograph.created_at <= end_dt,
    ).count()

    total_count = manual_count + tutorial_count + monograph_count

    return StatisticsResponse(
        entity="faculty",
        value=faculty_code,
        date_from=date_from,
        date_to=date_to,
        manual_count=manual_count,
        tutorial_count=tutorial_count,
        monograph_count=monograph_count,
        total_count=total_count,
    )


@router.get("/department", response_model=StatisticsResponse)
def count_by_department(
    department_name: str = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть больше date_to")

    start_dt, end_dt = build_datetime_range(date_from, date_to)

    manual_count = db.query(Manual).filter(
        Manual.department_name == department_name,
        Manual.created_at >= start_dt,
        Manual.created_at <= end_dt,
    ).count()

    tutorial_count = db.query(Tutorial).filter(
        Tutorial.department_name == department_name,
        Tutorial.created_at >= start_dt,
        Tutorial.created_at <= end_dt,
    ).count()

    monograph_count = db.query(Monograph).filter(
        Monograph.department_name == department_name,
        Monograph.created_at >= start_dt,
        Monograph.created_at <= end_dt,
    ).count()

    total_count = manual_count + tutorial_count + monograph_count

    return StatisticsResponse(
        entity="department",
        value=department_name,
        date_from=date_from,
        date_to=date_to,
        manual_count=manual_count,
        tutorial_count=tutorial_count,
        monograph_count=monograph_count,
        total_count=total_count,
    )


@router.get("/user", response_model=StatisticsResponse)
def count_by_user(
    fio_user: str = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть больше date_to")

    start_dt, end_dt = build_datetime_range(date_from, date_to)

    manual_count = db.query(Manual).filter(
        Manual.fio_user == fio_user,
        Manual.created_at >= start_dt,
        Manual.created_at <= end_dt,
    ).count()

    tutorial_count = db.query(Tutorial).filter(
        Tutorial.fio_user == fio_user,
        Tutorial.created_at >= start_dt,
        Tutorial.created_at <= end_dt,
    ).count()

    monograph_count = db.query(Monograph).filter(
        Monograph.fio_user == fio_user,
        Monograph.created_at >= start_dt,
        Monograph.created_at <= end_dt,
    ).count()

    total_count = manual_count + tutorial_count + monograph_count

    return StatisticsResponse(
        entity="user",
        value=fio_user,
        date_from=date_from,
        date_to=date_to,
        manual_count=manual_count,
        tutorial_count=tutorial_count,
        monograph_count=monograph_count,
        total_count=total_count,
    )