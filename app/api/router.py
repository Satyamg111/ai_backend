from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.agents import router as agents_router
from app.api.routes.uploads import (
    router as uploads_router
)
from app.api.routes.analytics import (
    router as analytics_router
)
from app.api.routes.config import (
    router as config_router
)

api_router = APIRouter()

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"]
)

api_router.include_router(
    chat_router,
    prefix="/chat",
    tags=["Chat"]
)

api_router.include_router(
    agents_router,
    prefix="/agents",
    tags=["Agents"]
)

api_router.include_router(
    uploads_router,
    prefix="/upload",
    tags=["Uploads"]
)

api_router.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["Analytics"]
)

api_router.include_router(
    config_router,
    prefix="/config",
    tags=["Config"]
)