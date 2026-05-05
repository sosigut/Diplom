from typing import Literal, List
from pydantic import BaseModel, Field


class ManualReviewer(BaseModel):
    degree: str = Field(..., description="Ученая степень, должность рецензента")
    fio: str = Field(..., description="ФИО рецензента")


class TitlePageRequest(BaseModel):
    # Методические указания
    manual_title: str
    discipline_name: str
    audience: Literal["студентов", "магистров"]
    direction_code: str
    direction_name: str
    city: str = "Курск"
    year: int

    udk: str
    compiler_name: str
    reviewers: List[ManualReviewer] = Field(..., min_length=1, description="Список рецензентов")
    description: str = Field(..., max_length=1000)


class TutorialReviewer(BaseModel):
    degree_position: str = Field(..., description="Ученая степень, должность рецензента")
    fio: str = Field(..., description="ФИО рецензента")


class TutorialDirection(BaseModel):
    code: str = Field(..., description="Код направления")
    faculty_name: str = Field(..., description="Название факультета / укрупненной группы")


class TutorialTitlePageRequest(BaseModel):
    # 1 страница
    author_name: str = Field(..., description="ФИО автора")
    tutorial_title: str = Field(..., description="Название учебного пособия")
    city: str = Field(default="Курск")
    year: int = Field(...)

    # 2 страница
    reviewers: List[TutorialReviewer] = Field(..., min_length=1)
    a_value: str = Field(..., description="Значение А")
    isbn: str = Field(..., description="Значение ISBN")
    directions: List[TutorialDirection] = Field(..., min_length=1)
    udk: str = Field(..., description="Значение УДК")
    bbk: str = Field(..., description="Значение ББК")
    description: str = Field(..., max_length=500, description="Краткое описание учебного пособия")


class MonographAuthor(BaseModel):
    fio: str = Field(..., description="ФИО автора")


class MonographTitlePageRequest(BaseModel):
    # 1 страница
    authors: List[MonographAuthor] = Field(..., min_length=1, description="Список авторов")
    monograph_title: str = Field(..., description="Тема монографии")
    city: str = Field(default="Курск")
    year: int = Field(...)

    # 2 страница
    udk: str = Field(..., description="Значение УДК")
    bbk: str = Field(..., description="Значение ББК")
    isbn: str = Field(..., description="Значение ISBN")
    description: str = Field(..., max_length=1000, description="Краткое описание монографии")