"""People (face cluster) router — GET /people/clusters"""
from fastapi import APIRouter, Depends, HTTPException
from routes.auth import current_user
from services import cluster_service
from services.face_service import index_unprocessed_photos
from services.database import connection

router = APIRouter(prefix="/people", tags=["People"])


@router.get("/clusters")
def list_clusters(user=Depends(current_user)):
    """Return all unique-person clusters for the authenticated user."""
    # Backfill photos uploaded before face indexing was wired into album and
    # gallery uploads. This makes the People page work for existing albums.
    with connection() as db:
        rows = db.execute(
            "SELECT image_url FROM gallery_photos WHERE user_id = ?",
            (user["id"],),
        ).fetchall()
    try:
        index_unprocessed_photos(user["id"], [row["image_url"] for row in rows])
    except Exception as exc:
        raise HTTPException(503, f"Could not index photos for People: {exc}") from exc
    clusters = cluster_service.cluster_faces(user["id"])
    # Strip internal source_urls before returning
    return [
        {
            "cluster_id": c["cluster_id"],
            "face_thumbnail_url": c["face_thumbnail_url"],
            "photo_count": c["photo_count"],
        }
        for c in clusters
    ]


@router.get("/clusters/{cluster_id}/photos")
def cluster_photos(cluster_id: int, user=Depends(current_user)):
    """Return all photos containing the person identified by cluster_id."""
    photos = cluster_service.get_photos_for_cluster(user["id"], cluster_id)
    if photos is None:
        raise HTTPException(404, "Person not found")
    return {"photos": photos}
