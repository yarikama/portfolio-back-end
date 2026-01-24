from typing import Optional

from schemas.base import BaseSchema


class UploadData(BaseSchema):
    url: str
    filename: Optional[str] = None


class UploadResponse(BaseSchema):
    data: UploadData


class DeleteResponse(BaseSchema):
    message: str
