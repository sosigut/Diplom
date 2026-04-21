from typing import Literal

from pydantic import BaseModel, Field


class TitlePageRequest(BaseModel):
    manual_title: str = Field(..., description="Тема методички")
    discipline_name: str = Field(..., description="Название дисциплины")
    audience: Literal["студентов", "магистров"] = Field(..., description="Для кого методичка")
    direction_code: str = Field(..., description="Например: 09.03.04")
    direction_name: str = Field(..., description="Например: Программная инженерия")
    city: str = Field(default="Курск")
    year: int = Field(..., description="Год выпуска")
    output_filename: str = Field(..., description="Имя скачиваемого файла без расширения или с .docx")