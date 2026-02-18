# dc-fastapi

Document Processing API — FastAPI sample integrating PostgreSQL, Redis, RabbitMQ, MinIO, and Gotenberg.

## Architecture

```
Upload file → MinIO (store original)
           → PostgreSQL (save metadata)
           → RabbitMQ (queue conversion task)
                ↓
           Worker picks up task
           → Gotenberg (convert to PDF)
           → MinIO (store converted PDF)
           → PostgreSQL (update status)
           → Redis (invalidate cache)
```

**Services:**
- **FastAPI backend** — REST API on port 8000
- **Worker** — RabbitMQ consumer for document conversion
- **PostgreSQL** — document metadata
- **Redis** — response caching
- **RabbitMQ** — task queue (management UI on port 15672)
- **MinIO** — file storage (console on port 9001)
- **Gotenberg** — document to PDF conversion

## Project structure

```
backend/app/
├── main.py                  # FastAPI app, lifespan, router includes
├── worker.py                # RabbitMQ consumer for document conversion
├── api/                     # API routes
│   ├── documents.py         # upload, get, list, download
│   └── health.py            # health check (all 5 services)
├── clients/                 # external service integrations
│   ├── gotenberg.py         # document → PDF conversion
│   ├── minio.py             # S3-compatible file storage
│   └── rabbitmq.py          # task queue publishing
├── core/                    # configuration
│   └── config.py            # pydantic-settings
├── database/                # database connections
│   ├── engines.py           # SQLAlchemy async engine
│   ├── sessions.py          # async session factory
│   └── redis.py             # Redis client
├── dependencies/            # FastAPI dependency injection
│   └── database.py          # get_db
├── models/                  # SQLAlchemy ORM models
│   ├── base.py              # DeclarativeBase
│   └── documents.py         # Document model
├── schemas/                 # Pydantic schemas
│   ├── documents.py         # DocumentResponse
│   └── health.py            # HealthResponse
└── services/                # business logic
    └── document_service.py  # DocumentService
```

## Quick start

```bash
cp .env.sample .env
vim .env
make up
```

## Commands

### Lifecycle

```
make d          # deploy (git pull + recreate)
make r          # recreate (build + stop + up)
make up         # start
make stop       # stop
make down       # stop and remove
make ps         # status
make l          # follow logs
```

### App

```
make shell          # bash shell in backend container
make logs-backend   # follow backend logs
make logs-worker    # follow worker logs
make test           # run smoke tests (health, upload, list)
make test-mickey    # run pymickey integration tests
```

## API

- `POST /documents/upload` — upload a file for conversion
- `GET /documents/` — list documents
- `GET /documents/{id}` — get document status (Redis-cached)
- `GET /documents/{id}/download` — download converted PDF
- `GET /health` — check all service connections
- `GET /docs` — Swagger UI
