import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.mdl_builder import build_and_save_mdl
from app.core.config import get_settings
from app.core.database import Base, async_engine
from app.routes import agent as agent_router
from app.routes import mdl as mdl_router
from app.routes import auth as auth_router
from app.routes import databases as databases_router
from app.core.models.auth import User
from app.core.models.tenant import DatabaseConnection
from app.core.models.mdl import MDLSchema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application startup and shutdown lifecycle.
    During startup, we initialize settings and log the start.
    During shutdown, we ensure the database engine is properly disposed.
    """
    settings = get_settings()
    logger.info("Starting up Database Intelligence Agent...")

    # The application is now general-purpose and ready to connect to any data source.
    yield

    logger.info("Shutting down Database Intelligence Agent...")
    await async_engine.dispose()


app = FastAPI(
    title="Database Intelligence Agent",
    description=(
        "A multi-tenant AI agent that translates natural language into SQL queries for any connected database. "
        "Powered by LangGraph, Groq LLM, and SQLAlchemy with dynamic Semantic MDL generation."
    ),
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(databases_router.router)
app.include_router(agent_router.router)
app.include_router(mdl_router.router)


@app.get("/health", tags=["Health"], summary="Service health check")
async def health():
    """
    Simple health check endpoint to verify database connectivity and MDL readiness.
    Returns the count of active MDL schemas in the system.
    """
    settings = get_settings()
    try:
        async with AsyncSession(async_engine) as session:
            await session.execute(text("SELECT 1"))
            mdl_count = await session.scalar(select(func.count(MDLSchema.id)))
        return {
            "status": "healthy",
            "database": "connected",
            "mdl_count": mdl_count,
        }
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
