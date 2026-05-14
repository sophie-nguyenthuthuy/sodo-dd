"""S3 / MinIO storage abstraction."""

from __future__ import annotations

import boto3
from botocore.client import Config

from app.config import settings

_s3 = None


def s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(
                s3={"addressing_style": "path" if settings.s3_force_path_style else "auto"}
            ),
        )
    return _s3


def upload_bytes(key: str, data: bytes, *, content_type: str = "application/octet-stream") -> str:
    s3().put_object(Bucket=settings.s3_bucket, Key=key, Body=data, ContentType=content_type)
    return key


def download_bytes(key: str) -> bytes:
    obj = s3().get_object(Bucket=settings.s3_bucket, Key=key)
    return obj["Body"].read()


def presigned_get(key: str, *, expires: int = 3600) -> str:
    return s3().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires,
    )
