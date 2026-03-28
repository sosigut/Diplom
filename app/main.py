from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine
from app.models import Faculty, Department, User, Manual, RefreshToken
from app.routers import auth, checker, admin

app = FastAPI(title="Diplom Checker API")

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(checker.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"message": "FastAPI works"}