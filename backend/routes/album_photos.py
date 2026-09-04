"""Album photos router — /events/{event_id}/albums/{album_id}/photos"""
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from routes.auth import current_user
from services import album_service

router = APIRouter(
    prefix="/events/{event_id}/albums/{album_id}/photos",
    tags=["Album Photos"],
)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class MapPhotosRequest(BaseModel):
    photo_ids: list[int] = Field(min_length=1, max_length=50)


@router.post("/upload", status_code=201)
async def upload_photos(
    event_id: int,
    album_id: int,
    files: list[UploadFile] = File(...),
    user=Depends(current_user),
):
    if not files:
        raise HTTPException(400, "Select at least one file")
    if len(files) > 20:
        raise HTTPException(400, "Maximum 20 files per upload")

    # Validate all files before uploading any
    errors = []
    for f in files:
        if f.content_type not in ALLOWED_TYPES:
            errors.append({"filename": f.filename, "reason": "unsupported file type"})
        else:
            content = await f.read()
            if len(content) > MAX_FILE_SIZE:
                errors.append({"filename": f.filename, "reason": "exceeds 10 MB"})
            else:
                # Reset file position for later upload
                import io
                f.file = io.BytesIO(content)
    if errors:
        raise HTTPException(400, detail={"errors": errors})

    result = album_service.upload_photos_to_album(user["id"], event_id, album_id, files)

    if isinstance(result, dict) and result.get("error") == "not_found":
        raise HTTPException(404, "Album not found")

    results = result.get("results", [])
    has_error = any(r["status"] == "error" for r in results)
    has_success = any(r["status"] == "success" for r in results)

    photos = [r for r in results if r["status"] == "success"]

    if has_error and has_success:
        return {"status": "partial", "photos": photos, "results": results}, 207
    if has_error and not has_success:
        raise HTTPException(400, detail={"errors": results})

    return {"photos": photos}


@router.post("/map")
def map_photos(
    event_id: int,
    album_id: int,
    data: MapPhotosRequest,
    user=Depends(current_user),
):
    result = album_service.map_photos_to_album(user["id"], event_id, album_id, data.photo_ids)
    if result is None:
        raise HTTPException(404, "Album not found")
    return result


@router.get("")
def list_photos(event_id: int, album_id: int, user=Depends(current_user)):
    photos = album_service.get_album_photos(user["id"], event_id, album_id)
    if photos is None:
        raise HTTPException(404, "Album not found")
    return {"photos": photos}


@router.delete("/{photo_id}")
def remove_photo(event_id: int, album_id: int, photo_id: int, user=Depends(current_user)):
    result = album_service.remove_photo_from_album(user["id"], event_id, album_id, photo_id)
    if result is None:
        raise HTTPException(404, "Album not found")
    if result is False:
        raise HTTPException(404, "Photo not associated with this album")
    return {"message": "Photo removed from album"}
