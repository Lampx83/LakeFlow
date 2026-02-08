# Load .env sớm nhất (trước mọi import dùng config)
import eduai.config.env  # noqa: F401, E402 — trigger load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from eduai.api.auth import router as auth_router
from eduai.api.search import router as search_router
from eduai.api.pipeline import router as pipeline_router
from eduai.api.system import router as system_router
from eduai.api.qdrant import router as qdrant_router
from eduai.api.admin import router as admin_router

from pathlib import Path
from eduai.runtime.config import runtime_config
from eduai.config.env import get_env



def create_app() -> FastAPI:
    """
    Khởi tạo FastAPI app cho EDUAI Backend
    """
    app = FastAPI(
        title="EDUAI Backend API",
        version="0.1.0",
        description="Backend AI & Data Services for EDUAI",
    )

    # -------------------------
    # Middleware
    # -------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # sau này siết domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ==================================================
    # BOOTSTRAP DATA_BASE_PATH (CRITICAL)
    # ==================================================
    try:
        base = Path(get_env("EDUAI_DATA_BASE_PATH")).resolve()
        runtime_config.set_data_base_path(base)
        print(f"[BOOT] DATA_BASE_PATH1 = {base}")
    except Exception as exc:
        print(f"[BOOT] DATA_BASE_PATH not set: {exc}")

    # -------------------------
    # Routers
    # -------------------------
    app.include_router(
        auth_router,
        prefix="/auth",
        tags=["auth"],
    )

    app.include_router(
        pipeline_router,
        prefix="/pipeline",
        tags=["pipeline"],
    )

    app.include_router(
        search_router,
        tags=["semantic-search"],
    )

    app.include_router(
        system_router,
    )
    app.include_router(
        qdrant_router,
    )
    app.include_router(
        admin_router,
    )

    # -------------------------
    # Health check
    # -------------------------
    @app.get("/health", tags=["system"])
    def health_check():
        return {"status": "ok"}

    return app


# App instance cho Uvicorn
app = create_app()
