"""People (face cluster) router — GET /people/clusters"""
from fastapi import APIRouter, Depends, HTTPException
from routes.auth import current_user
from services import cluster_service

router = APIRouter(prefix="/people", tags=["People"])


@router.get("/clusters")
def list_clusters(user=Depends(current_user)):
    """Return all unique-person clusters for the authenticated user."""
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
