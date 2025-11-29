"""Initialize the database schema."""
from app.config.logging import get_logger, setup_logging
from app.db.models import Base
from app.db.session import sync_engine

setup_logging()
logger = get_logger(__name__)


def init_database() -> None:
    """Initialize database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=sync_engine)
    logger.info("Database tables created successfully")


if __name__ == "__main__":
    init_database()
