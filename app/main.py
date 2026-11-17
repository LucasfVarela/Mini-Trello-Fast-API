from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api.v1.attachments.router import router as attachments_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.projects.router import router as projects_router
from app.api.v1.tasks.router import router as tasks_router
from app.core.db import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Mini Trello API",
    description="API REST para gestionar proyectos y tareas en un tablero estilo Trello.",
    version="1.0.0",
    lifespan=lifespan,
)

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth_router)
api_v1.include_router(projects_router)
api_v1.include_router(tasks_router)
api_v1.include_router(attachments_router)
app.include_router(api_v1)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
