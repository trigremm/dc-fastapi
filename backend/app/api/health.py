from fastapi import APIRouter
from sqlalchemy import text

from app.clients import gotenberg, minio, rabbitmq
from app.database.redis import redis_client
from app.database.sessions import async_session
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    checks = {}

    # PostgreSQL
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = str(e)

    # Redis
    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = str(e)

    # RabbitMQ
    try:
        await rabbitmq.check_connection()
        checks["rabbitmq"] = "ok"
    except Exception as e:
        checks["rabbitmq"] = str(e)

    # MinIO
    try:
        minio.check_connection()
        checks["minio"] = "ok"
    except Exception as e:
        checks["minio"] = str(e)

    # Gotenberg
    try:
        await gotenberg.check_connection()
        checks["gotenberg"] = "ok"
    except Exception as e:
        checks["gotenberg"] = str(e)

    all_ok = all(v == "ok" for v in checks.values())
    return HealthResponse(status="ok" if all_ok else "degraded", **checks)
