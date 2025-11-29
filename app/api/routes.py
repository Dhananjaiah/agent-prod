"""FastAPI routes for the insurance assistant."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.agents.insurance_agent import get_assistant
from app.config.logging import get_logger
from app.config.settings import get_settings
from app.db.session import AsyncSessionLocal
from app.models import ChatRequest, ChatResponse, HealthResponse

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the application status, environment, and database connection status.
    """
    db_status = "connected"

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "disconnected"

    return HealthResponse(
        status="ok",
        environment=settings.app_env,
        database=db_status,
    )


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint for the insurance assistant.

    Processes user messages and returns AI-generated responses
    based on insurance data from the database.

    Args:
        request: ChatRequest containing userId and message

    Returns:
        ChatResponse with the assistant's answer and supporting data
    """
    logger.info(
        "Received chat request",
        user_id=request.userId,
        message_length=len(request.message),
    )

    try:
        assistant = get_assistant()
        answer, data = await assistant.chat(request.userId, request.message)

        return ChatResponse(answer=answer, data=data)

    except Exception as e:
        logger.error(
            "Error processing chat request",
            error=str(e),
            user_id=request.userId,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request. Please try again.",
        )
