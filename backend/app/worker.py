import asyncio
import json

import aio_pika
from sqlalchemy import select

from app.clients import gotenberg, minio
from app.core.config import settings
from app.database.redis import redis_client
from app.database.sessions import async_session
from app.models import Document

QUEUE_NAME = "document_conversion"


async def process_document(document_id: str) -> None:
    async with async_session() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            print(f"Document {document_id} not found")
            return

        document.status = "processing"
        await db.commit()

        # Invalidate cache
        await redis_client.delete(f"doc:{document_id}")

        try:
            # Download original from MinIO
            original_data = minio.download_file(document.original_key)

            # Convert via Gotenberg
            pdf_data = await gotenberg.convert_to_pdf(document.filename, original_data)

            # Upload converted PDF to MinIO
            converted_key = f"converted/{document_id}/{document.filename.rsplit('.', 1)[0]}.pdf"
            minio.upload_file(converted_key, pdf_data, "application/pdf")

            # Update status
            document.converted_key = converted_key
            document.status = "done"
            await db.commit()

            print(f"Document {document_id} converted successfully")

        except Exception as e:
            document.status = "failed"
            document.error = str(e)
            await db.commit()
            print(f"Document {document_id} failed: {e}")

        # Invalidate cache
        await redis_client.delete(f"doc:{document_id}")


async def main() -> None:
    print("Worker starting...")
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)

        print(f"Listening on queue: {QUEUE_NAME}")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    body = json.loads(message.body.decode())
                    document_id = body["document_id"]
                    print(f"Processing document: {document_id}")
                    await process_document(document_id)


if __name__ == "__main__":
    asyncio.run(main())
