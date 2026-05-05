from datetime import date
from pydantic import BaseModel


class StatisticsResponse(BaseModel):
    entity: str
    value: str
    date_from: date
    date_to: date
    manual_count: int
    tutorial_count: int
    monograph_count: int
    total_count: int