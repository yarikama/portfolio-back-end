from api.dependencies import CurrentAdmin
from fastapi import APIRouter, File, UploadFile
from schemas.upload import DeleteResponse, UploadData, UploadResponse
from services.storage import storage_service

router = APIRouter()


@router.post("/admin/upload/image", response_model=UploadResponse)
async def upload_image(
    _admin: CurrentAdmin,
    file: UploadFile = File(...),
    folder: str = "images",
):
    """Upload an image to R2 storage. Returns the public URL."""
    url = await storage_service.upload_image(file, folder)
    return UploadResponse(data=UploadData(url=url, filename=file.filename))


@router.delete("/admin/upload/image", response_model=DeleteResponse)
async def delete_image(
    _admin: CurrentAdmin,
    url: str,
):
    """Delete an image from R2 storage by its URL."""
    await storage_service.delete_image(url)
    return DeleteResponse(message="Image deleted successfully")
