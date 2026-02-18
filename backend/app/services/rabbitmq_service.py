import json

import aio_pika

from app.config import settings

QUEUE_NAME = "document_conversion"


async def publish_task(document_id: str) -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue(QUEUE_NAME, durable=True)
        message = aio_pika.Message(
            body=json.dumps({"document_id": document_id}).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await channel.default_exchange.publish(message, routing_key=QUEUE_NAME)


async def check_connection() -> bool:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        return True
