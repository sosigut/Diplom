from pydantic import BaseModel, Field


class FacultyCreate(BaseModel):
    faculty_name: str = Field(..., min_length=2, max_length=255)
    faculty_code: int
    dean_fio: str = Field(..., min_length=5, max_length=255)


class FacultyResponse(BaseModel):
    id_faculty: int
    faculty_name: str
    faculty_code: int
    dean_fio: str
    manual_count: int

    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    department_name: str = Field(..., min_length=2, max_length=255)
    department_code: int
    faculty_code: int


class DepartmentResponse(BaseModel):
    id_department: int
    department_name: str
    department_code: int
    manual_count: int
    id_faculty: int

    class Config:
        from_attributes = True