from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserInfo(BaseModel):
    id_user: int
    email: EmailStr
    role: str
    faculty_name: str
    department_name: str
    created_at: datetime

    class Config:
        from_attributes = True