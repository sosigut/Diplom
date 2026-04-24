from pydantic import BaseModel, Field


class FacultyCreate(BaseModel):
    faculty_name: str = Field(..., min_length=2, max_length=255)
    faculty_code: str = Field(..., pattern=r'^\d{2}\.\d{2}\.\d{2}$')  # маска __.__.__
    dean_fio: str = Field(..., min_length=5, max_length=255)


class FacultyResponse(BaseModel):
    id_faculty: int
    faculty_name: str
    faculty_code: str
    dean_fio: str
    manual_count: int

    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    department_name: str = Field(..., min_length=2, max_length=255)
    faculty_code: str = Field(..., pattern=r'^\d{2}\.\d{2}\.\d{2}$')


class DepartmentResponse(BaseModel):
    id_department: int
    department_name: str
    manual_count: int
    id_faculty: int

    class Config:
        from_attributes = True