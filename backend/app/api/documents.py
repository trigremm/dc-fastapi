import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import minio
from app.dependencies.database import get_db
from app.schemas.documents import DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(file: UploadFile, db: AsyncSession = Depends(get_db)):
    data = await file.read()
    service = DocumentService(db)
    document = await service.upload(file.filename, data, file.content_type or "application/octet-stream")
    return document


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = DocumentService(db)
    document = await service.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/")
async def list_documents(db: AsyncSession = Depends(get_db)):
    service = DocumentService(db)
    documents = await service.list()
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{document_id}/download")
async def download_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = DocumentService(db)
    document = await service.get_for_download(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != "done" or not document.converted_key:
        raise HTTPException(status_code=400, detail=f"Document not ready: status={document.status}")

    data = minio.download_file(document.converted_key)
    pdf_filename = document.filename.rsplit(".", 1)[0] + ".pdf"

    return StreamingResponse(
        iter([data]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pdf_filename}"'},
    )
