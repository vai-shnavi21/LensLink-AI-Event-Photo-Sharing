"""Public event galleries and owner watermark controls."""
import os
from urllib.parse import quote
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from routes.auth import current_user
from services.database import connection
from services.cloudinary_service import upload_selfie
from services.face_service import generate_selfie_embedding_from_cloud, search_faces_multi

router = APIRouter(tags=["Sharing"])

DEFAULT = {"enabled": False, "image_url": None, "secondary_image_url": None,
           "text_value": None, "position": "bottom-right", "opacity": 45,
           "preview_enabled": True, "download_enabled": True}

class WatermarkUpdate(BaseModel):
    enabled: bool = False
    image_url: Optional[str] = Field(default=None, max_length=1000)
    secondary_image_url: Optional[str] = Field(default=None, max_length=1000)
    text_value: Optional[str] = Field(default=None, max_length=120)
    position: str = Field(default="bottom-right", pattern="^(top-left|top-right|bottom-left|bottom-right|center|tiled)$")
    opacity: int = Field(default=45, ge=10, le=90)
    preview_enabled: bool = True
    download_enabled: bool = True

def _settings(user_id, album_id=None):
    with connection() as db:
        row = db.execute("SELECT enabled,image_url,secondary_image_url,text_value,position,opacity,preview_enabled,download_enabled FROM watermark_settings WHERE user_id=? AND album_id IS NOT DISTINCT FROM ?", (user_id, album_id)).fetchone()
        if not row and album_id is not None:
            row = db.execute("SELECT enabled,image_url,secondary_image_url,text_value,position,opacity,preview_enabled,download_enabled FROM watermark_settings WHERE user_id=? AND album_id IS NULL", (user_id,)).fetchone()
    return dict(row) if row else DEFAULT.copy()

def _watermarked_url(url, settings):
    """Text watermark uses Cloudinary's delivery transformation; logo URLs are rendered by clients."""
    if not settings["enabled"] or not settings.get("text_value") or "/upload/" not in url:
        return url
    text = quote(settings["text_value"], safe="")
    gravity = {"top-left":"north_west", "top-right":"north_east", "bottom-left":"south_west", "bottom-right":"south_east", "center":"center", "tiled":"center"}[settings["position"]]
    transform = f"l_text:Arial_36_bold:{text},co_white,g_{gravity},o_{settings['opacity']},x_32,y_32"
    return url.replace("/upload/", f"/upload/{transform}/", 1)

def _download_url(url):
    return url.replace("/upload/", "/upload/fl_attachment/", 1) if "/upload/" in url else url

@router.get("/events/{event_id}/share")
def owner_share(event_id: int, user=Depends(current_user)):
    with connection() as db:
        row = db.execute("SELECT share_token FROM events WHERE id=? AND user_id=?", (event_id, user["id"])).fetchone()
    if not row: raise HTTPException(404, "Event not found")
    return {"token": str(row["share_token"])}

@router.get("/public/events/{token}")
def public_event(token: str):
    with connection() as db:
        event = db.execute("SELECT id,user_id,name,TO_CHAR(event_date, 'YYYY-MM-DD') AS event_date,description FROM events WHERE share_token=?", (token,)).fetchone()
        if not event: raise HTTPException(404, "This gallery link is invalid or has expired")
        albums = db.execute("SELECT id,name,description FROM albums WHERE event_id=? ORDER BY created_at", (event["id"],)).fetchall()
        result = []
        for album in albums:
            setting = _settings(event["user_id"], album["id"])
            photos = db.execute("SELECT gp.id,gp.title,gp.image_url,gp.thumbnail_url FROM gallery_photos gp JOIN album_photos ap ON ap.photo_id=gp.id WHERE ap.album_id=? ORDER BY ap.created_at", (album["id"],)).fetchall()
            result.append({**dict(album), "watermark": setting, "photos": [{**dict(p), "preview_url": _watermarked_url(p["thumbnail_url"] or p["image_url"], setting), "download_url": _download_url(_watermarked_url(p["image_url"], setting) if setting["download_enabled"] else p["image_url"])} for p in photos]})
    return {"event": dict(event), "albums": result}

@router.post("/public/events/{token}/search")
async def public_find_photos(token: str, files: list[UploadFile] = File(...)):
    if not files or len(files) > 10:
        raise HTTPException(400, "Upload between 1 and 10 selfies")
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if any(file.content_type not in allowed for file in files):
        raise HTTPException(400, "Use JPG, PNG, or WebP selfies")
    with connection() as db:
        event = db.execute("SELECT id,user_id FROM events WHERE share_token=?", (token,)).fetchone()
    if not event: raise HTTPException(404, "This gallery link is invalid or has expired")
    embeddings = []
    for file in files:
        try:
            uploaded = upload_selfie(file.file, file.filename or "guest-selfie.jpg", user_id=event["user_id"])
            embeddings.append(generate_selfie_embedding_from_cloud(uploaded["secure_url"]))
        except Exception:
            embeddings.append(None)
    matched, errors = search_faces_multi(embeddings, owner_user_id=event["user_id"], search_scope="event", scope_id=event["id"])
    return {"matched_photos": matched, "selfie_errors": [error for error in errors if error]}

@router.get("/watermark/settings")
def profile_watermark(user=Depends(current_user)):
    return _settings(user["id"])

@router.put("/watermark/settings")
def update_profile_watermark(data: WatermarkUpdate, user=Depends(current_user)):
    with connection() as db:
        row = db.execute("""INSERT INTO watermark_settings(user_id,album_id,enabled,image_url,secondary_image_url,text_value,position,opacity,preview_enabled,download_enabled)
        VALUES(?,NULL,?,?,?,?,?,?,?,?) ON CONFLICT (user_id, (COALESCE(album_id, -1))) DO UPDATE SET enabled=EXCLUDED.enabled,image_url=EXCLUDED.image_url,secondary_image_url=EXCLUDED.secondary_image_url,text_value=EXCLUDED.text_value,position=EXCLUDED.position,opacity=EXCLUDED.opacity,preview_enabled=EXCLUDED.preview_enabled,download_enabled=EXCLUDED.download_enabled
        RETURNING enabled,image_url,secondary_image_url,text_value,position,opacity,preview_enabled,download_enabled""", (user["id"], data.enabled, data.image_url, data.secondary_image_url, data.text_value, data.position, data.opacity, data.preview_enabled, data.download_enabled)).fetchone()
    return dict(row)

@router.post("/watermark/upload")
async def upload_watermark(file: UploadFile = File(...), user=Depends(current_user)):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(400, "Use a JPG, PNG, or WebP watermark image")
    if not all(os.getenv(k) for k in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")):
        raise HTTPException(503, "Cloudinary is not configured. Add backend/.env credentials.")
    import cloudinary
    import cloudinary.uploader
    cloudinary.config(cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"], api_key=os.environ["CLOUDINARY_API_KEY"], api_secret=os.environ["CLOUDINARY_API_SECRET"], secure=True)
    result = cloudinary.uploader.upload(file.file, folder=f"ai-event-gallery/watermarks/user-{user['id']}")
    return {"image_url": result["secure_url"]}

@router.get("/events/{event_id}/albums/{album_id}/watermark")
def album_watermark(event_id: int, album_id: int, user=Depends(current_user)):
    with connection() as db:
        owned = db.execute("SELECT 1 FROM albums a JOIN events e ON e.id=a.event_id WHERE a.id=? AND a.event_id=? AND e.user_id=?", (album_id,event_id,user["id"])).fetchone()
    if not owned: raise HTTPException(404, "Album not found")
    return _settings(user["id"], album_id)

@router.put("/events/{event_id}/albums/{album_id}/watermark")
def update_album_watermark(event_id: int, album_id: int, data: WatermarkUpdate, user=Depends(current_user)):
    with connection() as db:
        owned = db.execute("SELECT 1 FROM albums a JOIN events e ON e.id=a.event_id WHERE a.id=? AND a.event_id=? AND e.user_id=?", (album_id,event_id,user["id"])).fetchone()
        if not owned: raise HTTPException(404, "Album not found")
        row = db.execute("""INSERT INTO watermark_settings(user_id,album_id,enabled,image_url,secondary_image_url,text_value,position,opacity,preview_enabled,download_enabled)
        VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT (user_id, (COALESCE(album_id, -1))) DO UPDATE SET enabled=EXCLUDED.enabled,image_url=EXCLUDED.image_url,secondary_image_url=EXCLUDED.secondary_image_url,text_value=EXCLUDED.text_value,position=EXCLUDED.position,opacity=EXCLUDED.opacity,preview_enabled=EXCLUDED.preview_enabled,download_enabled=EXCLUDED.download_enabled
        RETURNING enabled,image_url,secondary_image_url,text_value,position,opacity,preview_enabled,download_enabled""", (user["id"],album_id,data.enabled,data.image_url,data.secondary_image_url,data.text_value,data.position,data.opacity,data.preview_enabled,data.download_enabled)).fetchone()
    return dict(row)
