from app.database.session import engine, Base, AsyncSessionLocal
from app.models import *  # Import all models to register them on Base.metadata
from app.database.seed_data import seed_initial_data
from app.core.logging import logger

async def init_db():
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")

    # Run seed data
    async with AsyncSessionLocal() as session:
        try:
            await seed_initial_data(session)
            logger.info("Initial seed data checked/loaded successfully.")
        except Exception as e:
            logger.error(f"Error seeding database: {e}", exc_info=True)
            await session.rollback()
