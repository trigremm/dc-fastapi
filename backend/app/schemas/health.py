from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    postgres: str
    redis: str
    rabbitmq: str
    minio: str
    gotenberg: str
