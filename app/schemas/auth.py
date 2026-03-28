from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    fio: str = Field(min_length=8, max_length=128)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    faculty_code: int
    department_code: int
    role: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
