from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    fio: str = Field(min_length=8, max_length=128)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    faculty_code: str
    department_name: str = Field(min_length=2, max_length=255)
    role: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
