from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://docproc:docproc@postgres:5432/docproc"
    redis_url: str = "redis://redis:6379/0"
    rabbitmq_url: str = "amqp://rabbit:rabbit@rabbitmq:5672/"
    minio_endpoint: str = "minio:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"
    minio_bucket: str = "documents"
    gotenberg_url: str = "http://gotenberg:3000"


settings = Settings()
