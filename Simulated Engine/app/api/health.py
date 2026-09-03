from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
    }
