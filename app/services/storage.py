import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import aioboto3
from aiobotocore.config import AioConfig
from core import config
from fastapi import HTTPException, UploadFile
from services.images import WIDTHS, is_original, variant_key

# botocore waits 60 s to connect by default: far too long for a request.
TIMEOUTS = AioConfig(connect_timeout=5, read_timeout=30, retries={"max_attempts": 3})

# Keys are unique per upload and never rewritten, so browsers and Cloudflare
# may keep variants for good.
IMMUTABLE = "public, max-age=31536000, immutable"


class R2StorageService:
    def __init__(self):
        self.endpoint_url = f"https://{config.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        self.bucket_name = config.R2_BUCKET_NAME
        self.public_url = config.R2_PUBLIC_URL

    @asynccontextmanager
    async def _client(self):
        session = aioboto3.Session()
        async with session.client(  # type: ignore[attr-defined]
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=config.R2_ACCESS_KEY_ID,
            aws_secret_access_key=config.R2_SECRET_ACCESS_KEY,
            region_name="auto",
            config=TIMEOUTS,
        ) as s3:
            yield s3

    def key_for(self, url: str) -> str:
        return url.removeprefix(f"{self.public_url}/")

    async def upload_image(self, file: UploadFile, folder: str = "images") -> str:
        """Upload an image to R2 and return the public URL."""
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(400, f"Unsupported file type: {file.content_type}")

        # Generate unique filename
        if file.filename and "." in file.filename:
            ext = file.filename.split(".")[-1]
        else:
            ext = "jpg"
        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex[:8]
        key = f"{folder}/{timestamp}/{unique_id}.{ext}"

        async with self._client() as s3:
            await s3.upload_fileobj(
                file.file,
                self.bucket_name,
                key,
                ExtraArgs={"ContentType": file.content_type},
            )

        return f"{self.public_url}/{key}"

    async def delete_image(self, url: str) -> bool:
        """Delete an image, and its WebP variants, by its public URL."""
        key = self.key_for(url)
        keys = [key]
        if is_original(key):
            keys += [variant_key(key, width) for width in WIDTHS]
        async with self._client() as s3:
            # Deleting a key that does not exist is not an error in S3.
            await s3.delete_objects(
                Bucket=self.bucket_name,
                Delete={"Objects": [{"Key": k} for k in keys], "Quiet": True},
            )
        return True

    async def read(self, key: str) -> bytes:
        async with self._client() as s3:
            response = await s3.get_object(Bucket=self.bucket_name, Key=key)
            async with response["Body"] as body:
                return await body.read()

    async def write(self, key: str, data: bytes, content_type: str) -> None:
        async with self._client() as s3:
            await s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
                CacheControl=IMMUTABLE,
            )

    async def list_keys(self) -> list[str]:
        keys = []
        async with self._client() as s3:
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=self.bucket_name):
                keys += [item["Key"] for item in page.get("Contents", [])]
        return keys


storage_service = R2StorageService()
