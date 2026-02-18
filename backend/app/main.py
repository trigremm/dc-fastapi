from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.dependencies import async_session, engine, redis_client
from app.models import Base
from app.routers import documents, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables, verify connections
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        await session.execute(text("SELECT 1"))

    await redis_client.ping()

    yield

    # Shutdown
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title="Document Processing API",
    description="FastAPI sample with PostgreSQL, Redis, RabbitMQ, MinIO, Gotenberg",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(documents.router)
