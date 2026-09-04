import os
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from routes.auth import current_user
from services.database import connection
router=APIRouter(prefix="/gallery",tags=["My Gallery"])
def uploader():
    if not all(os.getenv(k) for k in ("CLOUDINARY_CLOUD_NAME","CLOUDINARY_API_KEY","CLOUDINARY_API_SECRET")): raise HTTPException(503,"Cloudinary is not configured. Add backend/.env credentials.")
    import cloudinary, cloudinary.uploader
    cloudinary.config(cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],api_key=os.environ["CLOUDINARY_API_KEY"],api_secret=os.environ["CLOUDINARY_API_SECRET"],secure=True)
    return cloudinary.uploader
@router.post("/upload")
async def upload(files:list[UploadFile]=File(...),user=Depends(current_user)):
    client=uploader(); photos=[]
    for file in files:
        if file.content_type not in {"image/jpeg","image/png","image/webp","image/gif"}: raise HTTPException(400,f"{file.filename}: unsupported image type")
        result=client.upload(file.file,folder=f"ai-event-gallery/user-{user['id']}")
        title=Path(file.filename or "Photo").stem
        with connection() as db: photo_id=db.execute("INSERT INTO gallery_photos(user_id,public_id,image_url,thumbnail_url,title) VALUES(?,?,?,?,?) RETURNING id",(user["id"],result["public_id"],result["secure_url"],result["secure_url"],title)).fetchone()["id"]
        photos.append({"id":photo_id,"title":title,"image_url":result["secure_url"],"thumbnail_url":result["secure_url"]})
    return {"message":f"Uploaded {len(photos)} photo(s)","photos":photos}
@router.get("")
def list_photos(user=Depends(current_user)):
    with connection() as db:
        rows = db.execute(
            "SELECT id,title,image_url,thumbnail_url,created_at FROM gallery_photos WHERE user_id=? AND album_only = FALSE ORDER BY id DESC",
            (user["id"],)
        ).fetchall()
    return {"photos":[dict(x) for x in rows]}
@router.get("/{photo_id}")
def single(photo_id:int,user=Depends(current_user)):
    with connection() as db: row=db.execute("SELECT id,title,image_url,thumbnail_url,created_at FROM gallery_photos WHERE id=? AND user_id=?",(photo_id,user["id"])).fetchone()
    if not row: raise HTTPException(404,"Photo not found")
    return dict(row)

@router.delete("/{photo_id}")
def delete_photo(photo_id: int, user=Depends(current_user)):
    """Delete a gallery image only when it belongs to the signed-in user."""
    with connection() as db:
        row = db.execute("SELECT public_id FROM gallery_photos WHERE id=? AND user_id=?", (photo_id, user["id"])).fetchone()
        if not row:
            raise HTTPException(404, "Photo not found")
        db.execute("DELETE FROM gallery_photos WHERE id=? AND user_id=?", (photo_id, user["id"]))
    try:
        uploader().destroy(row["public_id"], resource_type="image", invalidate=True)
    except Exception:
        pass
    return {"message": "Photo deleted"}


@router.post("/add-from-album")
def add_to_gallery(body: dict, user=Depends(current_user)):
    """Move selected album photos into My Gallery (set album_only=FALSE)."""
    photo_ids = body.get("photo_ids", [])
    if not photo_ids:
        raise HTTPException(422, "No photo IDs provided")
    with connection() as db:
        for photo_id in photo_ids:
            db.execute(
                "UPDATE gallery_photos SET album_only = FALSE WHERE id = ? AND user_id = ?",
                (photo_id, user["id"])
            )
    return {"message": f"{len(photo_ids)} photo(s) added to your gallery"}
