from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import create_db_and_tables
from app.routers import (
    auth,
    decisions,
    features,
    feedback,
    goals,
    milestones,
    settings as settings_router,
    state,
    tasks,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Topaí API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")


@api.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


api.include_router(auth.router)
api.include_router(state.router)
api.include_router(tasks.router)
api.include_router(goals.router)
api.include_router(milestones.router)
api.include_router(features.router)
api.include_router(feedback.router)
api.include_router(decisions.router)
api.include_router(settings_router.router)

app.include_router(api)
