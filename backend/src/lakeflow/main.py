import lakeflow.config.env  # noqa: F401, E402 — trigger load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from lakeflow.i18n import http_exception_handler

# Routers
from lakeflow.api.auth import router as auth_router
from lakeflow.api.search import router as search_router
from lakeflow.api.pipeline import router as pipeline_router
from lakeflow.api.system import router as system_router
from lakeflow.api.qdrant import router as qdrant_router
from lakeflow.api.admin import router as admin_router
from lakeflow.api.inbox import router as inbox_router
from lakeflow.api.admission_agent import router as admission_agent_router
from lakeflow.api.library_document_agent import router as library_document_agent_router
from lakeflow.api.library_regulation_agent import router as library_regulation_agent_router
from lakeflow.api.research_khcn_regulation_agent import router as research_khcn_regulation_agent_router

import os
from pathlib import Path
from lakeflow.runtime.config import runtime_config



def create_app() -> FastAPI:
    """
    Initialize FastAPI app for LakeFlow Backend.
    """
    app = FastAPI(
        title="LakeFlow Backend API",
        version="0.1.0",
        description="Backend AI & Data Services for LakeFlow",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # restrict domains later
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(HTTPException, http_exception_handler)

    base_str = os.getenv("LAKE_ROOT", "/data")
    base = Path(base_str).expanduser().resolve()
    runtime_config.set_data_base_path(base)
    print(f"[BOOT] DATA_BASE_PATH = {base}")

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
    app.include_router(library_document_agent_router)
    app.include_router(library_regulation_agent_router)
    app.include_router(research_khcn_regulation_agent_router)

    @app.get("/health", tags=["system"])
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()
