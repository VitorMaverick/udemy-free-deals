import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from sqlalchemy import select

from app.config import settings
from app.database import Base, engine, async_session
from app.models import AdminUser
from app.auth import hash_password
from app.routers import admin, courses, posts
from app.routers.promoter import router as promoter_router
from app.services.scheduler import start_scheduler

STATIC_DIR = Path("/app/static") if os.path.exists("/app/static") else Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Criar tabelas (dev)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed admin user (cria ou atualiza senha)
    async with async_session() as session:
        result = await session.execute(select(AdminUser).where(AdminUser.username == settings.admin_username))
        user = result.scalar_one_or_none()
        if user:
            user.hashed_password = hash_password(settings.admin_password)
            await session.commit()
            logger.info(f"Admin user '{settings.admin_username}' senha atualizada")
        else:
            session.add(AdminUser(
                username=settings.admin_username,
                hashed_password=hash_password(settings.admin_password),
            ))
            await session.commit()
            logger.info(f"Admin user '{settings.admin_username}' criado")

    start_scheduler()
    logger.info("Aplicação iniciada")
    yield
    logger.info("Aplicação encerrada")


app = FastAPI(title="Udemy Free Deals API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router)
app.include_router(admin.router)
app.include_router(posts.router)
app.include_router(promoter_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve frontend static files (production only)
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve index.html for any non-API route (SPA fallback)."""
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
