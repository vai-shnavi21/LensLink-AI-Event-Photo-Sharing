"""
Face clustering service.

Clusters all face embeddings for a user into groups of unique people
using a greedy nearest-neighbour algorithm with cosine similarity ≥ 0.60.
No new images are uploaded; face thumbnails are generated via Cloudinary
URL transformations.
"""
import json
import re
from urllib.parse import urlparse

import numpy as np

from services.database import connection

SIMILARITY_THRESHOLD = 0.60


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _bbox_area(bbox: list) -> float:
    """bbox is [x1, y1, x2, y2]."""
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def _cloudinary_crop_url(source_url: str, bbox: list, size: int = 200) -> str:
    """
    Build a Cloudinary transformation URL that crops to the face bounding box.
    Bounding box is in original image coordinates (x1, y1, x2, y2).
    Adds 25% padding around the face for better framing.
    """
    x1, y1, x2, y2 = [float(v) for v in bbox]

    w = x2 - x1
    h = y2 - y1

    # Skip degenerate boxes (width or height too small)
    if w < 10 or h < 10:
        return source_url

    # 25% padding
    pad_x = w * 0.25
    pad_y = h * 0.25
    ix1 = max(0, int(x1 - pad_x))
    iy1 = max(0, int(y1 - pad_y))
    iw = max(1, int(w + pad_x * 2))
    ih = max(1, int(h + pad_y * 2))

    transform = f"c_crop,x_{ix1},y_{iy1},w_{iw},h_{ih}/c_fill,w_{size},h_{size}"
    url = re.sub(r"(/upload/)", rf"\1{transform}/", source_url, count=1)
    return url if url != source_url else source_url


def cluster_faces(user_id: int) -> list[dict]:
    """
    Load all face embeddings for user_id, cluster them using greedy
    nearest-neighbour, and return cluster metadata.

    Returns a list of dicts sorted by photo_count descending:
      {
        "cluster_id": int,          # representative embedding row id
        "face_thumbnail_url": str,
        "photo_count": int,
        "source_urls": list[str],   # all unique photo URLs in this cluster
      }
    """
    with connection() as db:
        rows = db.execute(
            """
            SELECT id, source_url, embedding, bounding_box
            FROM face_embeddings
            WHERE owner_user_id = ?
            ORDER BY id ASC
            """,
            (user_id,),
        ).fetchall()

    if not rows:
        return []

    # Parse embeddings and bboxes
    faces = []
    for row in rows:
        raw_emb = row["embedding"]
        raw_bb = row["bounding_box"]
        emb = np.asarray(
            json.loads(raw_emb) if isinstance(raw_emb, str) else raw_emb,
            dtype="float32",
        )
        bbox = json.loads(raw_bb) if isinstance(raw_bb, str) else raw_bb
        faces.append({
            "id": row["id"],
            "source_url": row["source_url"],
            "embedding": emb,
            "bbox": bbox,
        })

    # Greedy nearest-neighbour clustering
    # clusters: list of {"rep": face_dict, "members": [face_dict]}
    clusters = []

    for face in faces:
        matched = None
        best_score = -1.0
        for cluster in clusters:
            score = _cosine_similarity(face["embedding"], cluster["rep"]["embedding"])
            if score >= SIMILARITY_THRESHOLD and score > best_score:
                best_score = score
                matched = cluster
        if matched is not None:
            matched["members"].append(face)
            # Update representative to largest bounding-box face
            if _bbox_area(face["bbox"]) > _bbox_area(matched["rep"]["bbox"]):
                matched["rep"] = face
        else:
            clusters.append({"rep": face, "members": [face]})

    # Build result list
    results = []
    for cluster in clusters:
        rep = cluster["rep"]
        source_urls = list({m["source_url"] for m in cluster["members"]})
        photo_count = len(source_urls)
        thumbnail_url = _cloudinary_crop_url(rep["source_url"], rep["bbox"])
        results.append({
            "cluster_id": rep["id"],
            "face_thumbnail_url": thumbnail_url,
            "photo_count": photo_count,
            "source_urls": source_urls,
        })

    # Sort by photo_count descending
    results.sort(key=lambda c: c["photo_count"], reverse=True)
    return results


def get_photos_for_cluster(user_id: int, cluster_id: int) -> list[dict] | None:
    """
    Given a cluster_id (= representative face_embedding row id), re-run
    clustering and return gallery photos for that cluster.

    Returns None if cluster_id not found / not owned by user_id.
    Returns [] if cluster exists but no photos found.
    """
    clusters = cluster_faces(user_id)
    target = next((c for c in clusters if c["cluster_id"] == cluster_id), None)

    if target is None:
        return None

    source_urls = target["source_urls"]
    if not source_urls:
        return []

    with connection() as db:
        # Use ANY to fetch all matching photos in one query
        # psycopg supports passing a list for ANY
        placeholders = ",".join(["?" for _ in source_urls])
        rows = db.execute(
            f"""
            SELECT id, image_url, thumbnail_url, title
            FROM gallery_photos
            WHERE user_id = ? AND image_url IN ({placeholders})
            ORDER BY created_at DESC
            """,
            (user_id, *source_urls),
        ).fetchall()

    # Older event uploads were indexed in face_embeddings without a matching
    # gallery_photos row. Keep those existing photos visible while new uploads
    # are persisted correctly by the upload route.
    photos_by_url = {row["image_url"]: dict(row) for row in rows}
    photos = []
    for url in source_urls:
        photo = photos_by_url.get(url)
        if photo is None:
            filename = urlparse(url).path.rsplit("/", 1)[-1] or "Photo"
            photo = {
                "id": f"indexed:{url}",
                "image_url": url,
                "thumbnail_url": url,
                "title": filename,
            }
        photos.append(photo)
    return photos
