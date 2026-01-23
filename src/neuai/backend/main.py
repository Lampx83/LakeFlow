from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from neuai.backend.api.auth import router as auth_router
from neuai.api.search import router as search_router


def create_app() -> FastAPI:
    """
    Khởi tạo FastAPI app cho NEUAI Backend
    """
    app = FastAPI(
        title="NEUAI Backend API",
        version="0.1.0",
        description="Backend AI & Data Services for NEUAI",
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

    # -------------------------
    # Routers
    # -------------------------
    app.include_router(
        auth_router,
        prefix="/auth",
        tags=["auth"],
    )

    app.include_router(
        search_router,
        tags=["semantic-search"],
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
for r in app.routes:
    print(r.path)
