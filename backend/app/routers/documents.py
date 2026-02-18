import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, redis_client
from app.models import Document
from app.schemas import DocumentResponse
from app.services import minio_service, rabbitmq_service

router = APIRouter(prefix="/documents", tags=["documents"])

CACHE_TTL = 60


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(file: UploadFile, db: AsyncSession = Depends(get_db)):
    data = await file.read()
    doc_id = uuid.uuid4()
    original_key = f"originals/{doc_id}/{file.filename}"

    # Upload to MinIO
    minio_service.upload_file(original_key, data, file.content_type or "application/octet-stream")

    # Save metadata to PostgreSQL
    document = Document(
        id=doc_id,
        filename=file.filename,
        original_key=original_key,
        content_type=file.content_type or "application/octet-stream",
        status="pending",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Publish conversion task to RabbitMQ
    await rabbitmq_service.publish_task(str(doc_id))

    return document


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Check Redis cache
    cached = await redis_client.get(f"doc:{document_id}")
    if cached:
        return DocumentResponse.model_validate_json(cached)

    # Query PostgreSQL
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    response = DocumentResponse.model_validate(document)

    # Cache in Redis
    await redis_client.set(f"doc:{document_id}", response.model_dump_json(), ex=CACHE_TTL)

    return response


@router.get("/")
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()).limit(50))
    documents = result.scalars().all()
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{document_id}/download")
async def download_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != "done" or not document.converted_key:
        raise HTTPException(status_code=400, detail=f"Document not ready: status={document.status}")

    data = minio_service.download_file(document.converted_key)
    pdf_filename = document.filename.rsplit(".", 1)[0] + ".pdf"

    return StreamingResponse(
        iter([data]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf_filename}"'},
    )
