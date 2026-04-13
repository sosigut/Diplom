from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.db.base import Base
from app.db.session import engine
from app.models import Faculty, Department, User, Manual, RefreshToken
from app.routers import admin, auth, checker, statistics

app = FastAPI(title="Diplom Checker API")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(checker.router)
app.include_router(admin.router)
app.include_router(statistics.router)


@app.get("/")
def root():
    return FileResponse("app/templates/index.html")