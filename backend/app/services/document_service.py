import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import minio, rabbitmq
from app.database.redis import redis_client
from app.models import Document
from app.schemas.documents import DocumentResponse

CACHE_TTL = 60


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload(self, filename: str, data: bytes, content_type: str) -> Document:
        doc_id = uuid.uuid4()
        original_key = f"originals/{doc_id}/{filename}"

        minio.upload_file(original_key, data, content_type)

        document = Document(
            id=doc_id,
            filename=filename,
            original_key=original_key,
            content_type=content_type,
            status="pending",
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        await rabbitmq.publish_task(str(doc_id))

        return document

    async def get(self, document_id: uuid.UUID) -> Document:
        cached = await redis_client.get(f"doc:{document_id}")
        if cached:
            return DocumentResponse.model_validate_json(cached)

        result = await self.db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            return None

        response = DocumentResponse.model_validate(document)
        await redis_client.set(f"doc:{document_id}", response.model_dump_json(), ex=CACHE_TTL)

        return document

    async def list(self, limit: int = 50) -> list[Document]:
        result = await self.db.execute(
            select(Document).order_by(Document.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_for_download(self, document_id: uuid.UUID) -> Document | None:
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()
