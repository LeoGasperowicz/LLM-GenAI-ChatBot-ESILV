from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.settings import settings
from .routers import chat, admin


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
    )

    # CORS pour autoriser le frontend Streamlit
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:3000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Inclusion des routers
    app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
    app.include_router(admin.router, prefix=settings.API_V1_PREFIX)

    @app.get("/")
    async def root():
        return {"message": "ESILV Smart Assistant backend is running."}

    return app


app = create_app()