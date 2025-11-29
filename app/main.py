"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config.logging import get_logger, setup_logging
from app.config.settings import get_settings
from app.db.session import close_db, init_db

# Initialize logging
setup_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(
        "Starting application",
        environment=settings.app_env,
        host=settings.host,
        port=settings.port,
    )

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    yield

    # Cleanup
    await close_db()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Agentic Insurance Assistant",
    description="A production-grade AI-powered insurance chatbot with LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
# Note: In staging/production, configure specific allowed origins via environment
# For now, allowing all origins in development, empty in prod (configure as needed)
cors_origins = ["*"] if settings.app_env == "local" else []
if not settings.is_production:
    # In staging, allow common development origins
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Also add routes at root level for convenience
app.include_router(router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint returning application info."""
    return {
        "name": "Agentic Insurance Assistant",
        "version": "1.0.0",
        "environment": settings.app_env,
        "docs_url": "/docs",
    }
