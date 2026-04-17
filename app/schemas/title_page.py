from typing import Literal

from pydantic import BaseModel, Field


class TitlePageRequest(BaseModel):
    manual_title: str = Field(..., description="Название методички")
    discipline_name: str = Field(..., description="Название дисциплины")
    audience: Literal["студентов", "магистров"] = Field(..., description="Для кого методичка")
    city: str = Field(default="Курск")
    year: int = Field(..., description="Год выпуска")