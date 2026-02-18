# Load .env sớm nhất (trước mọi import dùng config)
import lakeflow.config.env  # noqa: F401, E402 — trigger load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from lakeflow.api.auth import router as auth_router
from lakeflow.api.search import router as search_router
from lakeflow.api.pipeline import router as pipeline_router
from lakeflow.api.system import router as system_router
from lakeflow.api.qdrant import router as qdrant_router
from lakeflow.api.admin import router as admin_router
from lakeflow.api.inbox import router as inbox_router
from lakeflow.api.admission_agent import router as admission_agent_router

import os
from pathlib import Path
from lakeflow.runtime.config import runtime_config



def create_app() -> FastAPI:
    """
    Khởi tạo FastAPI app cho LakeFlow Backend
    """
    app = FastAPI(
        title="LakeFlow Backend API",
        version="0.1.0",
        description="Backend AI & Data Services for LakeFlow",
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
    base_str = os.getenv("LAKEFLOW_DATA_BASE_PATH", "/data")
    base = Path(base_str).expanduser().resolve()
    runtime_config.set_data_base_path(base)
    print(f"[BOOT] DATA_BASE_PATH = {base}")

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
    app.include_router(
        inbox_router,
        prefix="/inbox",
        tags=["inbox"],
    )

    app.include_router(admission_agent_router)

    # -------------------------
    # Health check
    # -------------------------
    @app.get("/health", tags=["system"])
    def health_check():
        return {"status": "ok"}

    return app


# App instance cho Uvicorn
app = create_app()
