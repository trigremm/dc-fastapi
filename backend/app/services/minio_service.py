import io

import boto3
from botocore.config import Config

from app.config import settings

s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{settings.minio_endpoint}",
    aws_access_key_id=settings.minio_root_user,
    aws_secret_access_key=settings.minio_root_password,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)


def upload_file(key: str, data: bytes, content_type: str) -> None:
    s3_client.put_object(
        Bucket=settings.minio_bucket,
        Key=key,
        Body=io.BytesIO(data),
        ContentType=content_type,
    )


def download_file(key: str) -> bytes:
    response = s3_client.get_object(Bucket=settings.minio_bucket, Key=key)
    return response["Body"].read()


def check_connection() -> bool:
    s3_client.head_bucket(Bucket=settings.minio_bucket)
    return True
