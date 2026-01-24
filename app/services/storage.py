import uuid
from datetime import datetime

import aioboto3
from core import config
from fastapi import HTTPException, UploadFile


class R2StorageService:
    def __init__(self):
        self.endpoint_url = f"https://{config.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        self.bucket_name = config.R2_BUCKET_NAME
        self.public_url = config.R2_PUBLIC_URL

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

        # Upload to R2
        session = aioboto3.Session()
        async with session.client(  # type: ignore[attr-defined]
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=config.R2_ACCESS_KEY_ID,
            aws_secret_access_key=config.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        ) as s3:
            await s3.upload_fileobj(
                file.file,
                self.bucket_name,
                key,
                ExtraArgs={"ContentType": file.content_type},
            )

        return f"{self.public_url}/{key}"

    async def delete_image(self, url: str) -> bool:
        """Delete an image from R2 by its public URL."""
        # Extract key from URL
        key = url.replace(f"{self.public_url}/", "")

        session = aioboto3.Session()
        async with session.client(  # type: ignore[attr-defined]
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=config.R2_ACCESS_KEY_ID,
            aws_secret_access_key=config.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        ) as s3:
            await s3.delete_object(Bucket=self.bucket_name, Key=key)

        return True


storage_service = R2StorageService()
