from schemas.base import BaseSchema


class UploadData(BaseSchema):
    url: str
    filename: str | None = None


class UploadResponse(BaseSchema):
    data: UploadData


class DeleteResponse(BaseSchema):
    message: str
