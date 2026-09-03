from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.market import router as market_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.simulation import SimulationService
from app.storage import MemorySimulationStorage
from app.streaming.market import router as streaming_router

STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        if settings.database_url:
            from app.storage.postgres import PostgresSimulationStorage
            storage = PostgresSimulationStorage(
                settings.database_url, min_size=settings.database_pool_min_size,
                max_size=settings.database_pool_max_size,
            )
        else:
            storage = MemorySimulationStorage()
        service = SimulationService(
            storage=storage,
            persistence_enabled=bool(settings.database_url),
            queue_capacity=settings.persistence_queue_capacity,
            high_water_mark=settings.persistence_high_water_mark,
            low_water_mark=settings.persistence_low_water_mark,
            retry_limit=settings.persistence_retry_limit,
            retry_base_seconds=settings.persistence_retry_base_seconds,
            shutdown_timeout=settings.persistence_shutdown_timeout_seconds,
            history_page_limit=settings.history_page_limit,
            replay_min_speed=settings.replay_min_speed,
            replay_max_speed=settings.replay_max_speed,
        )
        application.state.simulation = service
        await service.startup()
        try:
            yield
        finally:
            await service.shutdown()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(market_router)
    app.include_router(streaming_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
