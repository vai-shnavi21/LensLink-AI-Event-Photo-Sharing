import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(DOTENV_PATH)

from services.face_service import (
    generate_selfie_embedding_from_cloud,
    index_unprocessed_photos,
    process_cloud_event_photos,
    search_faces,
    search_faces_multi,
)
from services.database import connection, setup_database
from services import event_service, album_service
from routes.auth import router as auth_router
from routes.gallery import router as gallery_router
from routes.upload import router as upload_router
from routes.events import router as events_router
from routes.albums import router as albums_router
from routes.album_photos import router as album_photos_router
from routes.people import router as people_router
from routes.auth import current_user
from services.cloudinary_service import upload_event_photo, upload_selfie

# ── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(title="AI Event Photo Sharing POC")
setup_database()

app.include_router(auth_router)
app.include_router(gallery_router)
app.include_router(upload_router)
app.include_router(events_router)
app.include_router(albums_router)
app.include_router(album_photos_router)
app.include_router(people_router)

# ── CORS ─────────────────────────────────────────────────────────────────────

frontend_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in frontend_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Home ─────────────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"status": "success", "message": "AI Event Photo Sharing Backend Running"}

# ── Upload Event Photos ───────────────────────────────────────────────────────

@app.post("/upload-event")
async def upload_event(
    files: list[UploadFile] = File(...),
    user=Depends(current_user),
):
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if not files:
        raise HTTPException(400, "Select at least one event photo")

    cloud_urls = []
    uploaded_photos = []
    for file in files:
        if file.content_type not in allowed_types:
            raise HTTPException(400, f"{file.filename}: unsupported image type")
        try:
            result = upload_event_photo(file.file, file.filename, user_id=user["id"])
        except Exception as exc:
            raise HTTPException(502, f"Failed to upload {file.filename} to Cloudinary") from exc
        cloud_urls.append(result["secure_url"])
        title = Path(file.filename or "Photo").stem
        # People and scoped searches resolve matches through gallery_photos.
        # Persist every event upload before indexing its faces so both flows
        # refer to the same owner-scoped photo record.
        with connection() as db:
            photo_id = db.execute(
                """
                INSERT INTO gallery_photos
                    (user_id, public_id, image_url, thumbnail_url, title, album_only)
                VALUES (?, ?, ?, ?, ?, FALSE)
                RETURNING id
                """,
                (user["id"], result["public_id"], result["secure_url"], result["secure_url"], title),
            ).fetchone()["id"]
        uploaded_photos.append({
            "id": photo_id,
            "filename": file.filename,
            "cloud_url": result["secure_url"],
            "public_id": result["public_id"],
        })

    process_cloud_event_photos(cloud_urls, owner_user_id=user["id"])
    return {"status": "success", "message": "Photos uploaded and indexed successfully", "photos": uploaded_photos}

# ── Search Face (multi-selfie + scoped) ───────────────────────────────────────

@app.post("/search")
async def search(
    files: list[UploadFile] = File(...),
    search_scope: str = Form(default="gallery"),
    scope_id: Optional[int] = Form(default=None),
    user=Depends(current_user),
):
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}

    if search_scope not in {"gallery", "event", "album"}:
        raise HTTPException(422, "search_scope must be gallery, event, or album")
    if search_scope in {"event", "album"} and scope_id is None:
        raise HTTPException(422, "Select an event or album before searching")

    if len(files) > 10:
        raise HTTPException(400, "Maximum is 10 selfies per request")

    # Validate scope ownership
    if search_scope == "event" and scope_id is not None:
        ev = event_service.get_event(user["id"], scope_id)
        if not ev:
            raise HTTPException(404, "Event not found or access denied")
    elif search_scope == "album" and scope_id is not None:
        # Find the event_id for this album then verify ownership
        from services.database import connection
        with connection() as db:
            row = db.execute(
                """
                SELECT al.id FROM albums al
                JOIN events ev ON ev.id = al.event_id
                WHERE al.id = ? AND ev.user_id = ?
                """,
                (scope_id, user["id"]),
            ).fetchone()
        if not row:
            raise HTTPException(404, "Album not found or access denied")

    # Index only legacy/unprocessed photos in the selected scope before
    # matching. Album uploads previously hid indexing errors, which left
    # visible images with no searchable face embeddings.
    with connection() as db:
        if search_scope == "event":
            photo_rows = db.execute(
                """
                SELECT DISTINCT gp.image_url
                FROM gallery_photos gp
                JOIN album_photos ap ON ap.photo_id = gp.id
                JOIN albums al ON al.id = ap.album_id
                WHERE al.event_id = ? AND gp.user_id = ?
                """,
                (scope_id, user["id"]),
            ).fetchall()
        elif search_scope == "album":
            photo_rows = db.execute(
                """
                SELECT gp.image_url FROM gallery_photos gp
                JOIN album_photos ap ON ap.photo_id = gp.id
                WHERE ap.album_id = ? AND gp.user_id = ?
                """,
                (scope_id, user["id"]),
            ).fetchall()
        else:
            photo_rows = db.execute(
                "SELECT image_url FROM gallery_photos WHERE user_id = ?",
                (user["id"],),
            ).fetchall()
    try:
        index_unprocessed_photos(user["id"], [row["image_url"] for row in photo_rows])
    except Exception as exc:
        raise HTTPException(503, f"Could not index photos for this search: {exc}") from exc

    # Upload all selfies and generate embeddings
    embeddings = []
    for file in files:
        if file.content_type not in allowed_types:
            embeddings.append(None)
            continue
        try:
            upload_result = upload_selfie(file.file, file.filename, user_id=user["id"])
            embedding = generate_selfie_embedding_from_cloud(upload_result["secure_url"])
            embeddings.append(embedding)
        except Exception:
            embeddings.append(None)

    matched_photos, selfie_errors = search_faces_multi(
        embeddings,
        threshold=0.60,
        top_k=50,
        owner_user_id=user["id"],
        search_scope=search_scope,
        scope_id=scope_id,
    )

    return {
        "status": "success",
        "matched_photos": matched_photos,
        "selfie_errors": [
            {"index": i, "message": msg} for i, msg in enumerate(selfie_errors) if msg
        ] or None,
    }

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
