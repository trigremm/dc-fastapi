import httpx

from app.core.config import settings


async def convert_to_pdf(filename: str, file_data: bytes) -> bytes:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.gotenberg_url}/forms/libreoffice/convert",
            files={"files": (filename, file_data)},
        )
        response.raise_for_status()
        return response.content


async def check_connection() -> bool:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{settings.gotenberg_url}/health")
        return response.status_code == 200
