from typing import Literal
from pydantic import BaseModel, Field


class TitlePageRequest(BaseModel):
    manual_title: str
    discipline_name: str
    audience: Literal["студентов", "магистров"]
    direction_code: str
    direction_name: str
    city: str = "Курск"
    year: int

    udk: str = Field(..., description="Значение УДК")
    compiler_name: str = Field(..., description="ФИО составителя")
    reviewer_name: str = Field(..., description="ФИО рецензента")
    reviewer_degree: str = Field(..., description="Ученая степень рецензента")
    description: str = Field(..., max_length=1000, description="Краткое описание")