from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.session import Base, engine
from app.services.runtime import create_runtime


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.ensure_directories()
    Base.metadata.create_all(bind=engine)
    app.state.runtime = create_runtime(settings)
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Transfer learning + FAISS + MLflow + LangGraph industrial defect intelligence.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=settings.api_prefix, tags=["FactoryLens"])


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "FactoryLens AI is running",
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
    }
