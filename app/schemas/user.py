from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserRegister(BaseModel):
    fio: str = Field(min_length=8, max_length=128)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    faculty_code: str = Field(..., pattern=r'^\d{2}\.\d{2}\.\d{2}$')
    department_name: str = Field(min_length=2, max_length=255)  # теперь название кафедры
    role: str

class UserInfo(BaseModel):
    id_user: int
    fio: str
    email: EmailStr
    role: str
    faculty_name: str
    department_name: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)