from fastapi import FastAPI
from app.routers import checker
from app.db.base import Base
from app.db.session import engine
from app.models import Faculty, Department, User, Manual

app = FastAPI(title="Diplom Checker API")

Base.metadata.create_all(bind=engine)
app.include_router(checker.router)


@app.get("/")
def root():
    return {"message": "FastAPI works"}