"""Album CRUD and photo association business logic."""
from pathlib import Path
from services.database import connection
from services.cloudinary_service import upload_event_photo


def _event_owned(db, user_id: int, event_id: int) -> bool:
    row = db.execute(
        "SELECT id FROM events WHERE id = ? AND user_id = ?",
        (event_id, user_id),
    ).fetchone()
    return row is not None


def _album_owned(db, user_id: int, event_id: int, album_id: int) -> bool:
    row = db.execute(
        """
        SELECT al.id FROM albums al
        JOIN events ev ON ev.id = al.event_id
        WHERE al.id = ? AND al.event_id = ? AND ev.user_id = ?
        """,
        (album_id, event_id, user_id),
    ).fetchone()
    return row is not None


# ── Album CRUD ──────────────────────────────────────────────────────────────

def create_album(user_id: int, event_id: int, name: str, description: str | None) -> dict | None:
    with connection() as db:
        if not _event_owned(db, user_id, event_id):
            return None
        row = db.execute(
            """
            INSERT INTO albums (event_id, name, description)
            VALUES (?, ?, ?)
            RETURNING id, event_id, name, description, created_at
            """,
            (event_id, name, description),
        ).fetchone()
    return dict(row)


def list_albums(user_id: int, event_id: int) -> list[dict] | None:
    with connection() as db:
        if not _event_owned(db, user_id, event_id):
            return None
        rows = db.execute(
            """
            SELECT al.id, al.event_id, al.name, al.description, al.created_at,
                   COUNT(ap.id) AS photo_count
            FROM albums al
            LEFT JOIN album_photos ap ON ap.album_id = al.id
            WHERE al.event_id = ?
            GROUP BY al.id
            ORDER BY al.created_at ASC
            """,
            (event_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def update_album(
    user_id: int,
    event_id: int,
    album_id: int,
    name: str | None = None,
    description: str | None = None,
) -> dict | None:
    fields, values = [], []
    if name is not None:
        fields.append("name = ?"); values.append(name)
    if description is not None:
        fields.append("description = ?"); values.append(description)
    if not fields:
        return None
    values.extend([album_id, event_id])
    with connection() as db:
        if not _event_owned(db, user_id, event_id):
            return None
        row = db.execute(
            f"""
            UPDATE albums SET {', '.join(fields)}
            WHERE id = ? AND event_id = ?
            RETURNING id, event_id, name, description, created_at
            """,
            tuple(values),
        ).fetchone()
    return dict(row) if row else None


def delete_album(user_id: int, event_id: int, album_id: int) -> bool:
    with connection() as db:
        if not _event_owned(db, user_id, event_id):
            return False
        cursor = db.execute(
            "DELETE FROM albums WHERE id = ? AND event_id = ?",
            (album_id, event_id),
        )
        return cursor.rowcount > 0


# ── Photo queries ────────────────────────────────────────────────────────────

def get_album_photos(user_id: int, event_id: int, album_id: int) -> list[dict] | None:
    with connection() as db:
        if not _album_owned(db, user_id, event_id, album_id):
            return None
        rows = db.execute(
            """
            SELECT gp.id, gp.image_url, gp.thumbnail_url, gp.title
            FROM gallery_photos gp
            JOIN album_photos ap ON ap.photo_id = gp.id
            WHERE ap.album_id = ?
            ORDER BY ap.created_at ASC
            """,
            (album_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Photo association ────────────────────────────────────────────────────────

def upload_photos_to_album(
    user_id: int,
    event_id: int,
    album_id: int,
    files: list,
) -> dict:
    """Upload new files to Cloudinary, persist in gallery_photos + album_photos."""
    from services.face_service import process_cloud_event_photos

    with connection() as db:
        if not _album_owned(db, user_id, event_id, album_id):
            return {"error": "not_found"}

    results = []
    cloud_urls = []

    for file in files:
        try:
            result = upload_event_photo(file.file, file.filename, user_id=user_id)
            title = Path(file.filename or "Photo").stem
            with connection() as db:
                photo_id = db.execute(
                    """
                    INSERT INTO gallery_photos (user_id, public_id, image_url, thumbnail_url, title, album_only)
                    VALUES (?, ?, ?, ?, ?, TRUE) RETURNING id
                    """,
                    (user_id, result["public_id"], result["secure_url"], result["secure_url"], title),
                ).fetchone()["id"]
                db.execute(
                    "INSERT INTO album_photos (album_id, photo_id) VALUES (?, ?)",
                    (album_id, photo_id),
                )
            cloud_urls.append(result["secure_url"])
            results.append({
                "status": "success",
                "id": photo_id,
                "image_url": result["secure_url"],
                "thumbnail_url": result["secure_url"],
            })
        except Exception as exc:
            results.append({"status": "error", "filename": file.filename, "reason": str(exc)})

    indexing = {"status": "not_needed"}
    if cloud_urls:
        try:
            indexed = process_cloud_event_photos(cloud_urls, owner_user_id=user_id)
            indexing = {
                "status": "complete" if indexed else "no_faces_detected",
            }
        except Exception as exc:
            # Uploads are already durable, so return them to the user. Do not
            # silently hide the indexing problem: Find Photos can retry the
            # same album automatically later.
            indexing = {"status": "failed", "message": str(exc)}

    return {"results": results, "indexing": indexing}


def map_photos_to_album(
    user_id: int,
    event_id: int,
    album_id: int,
    photo_ids: list[int],
) -> dict | None:
    with connection() as db:
        if not _album_owned(db, user_id, event_id, album_id):
            return None

        skipped = []
        associated_count = 0

        for photo_id in photo_ids:
            # Check existence
            photo = db.execute(
                "SELECT id, user_id FROM gallery_photos WHERE id = ?",
                (photo_id,),
            ).fetchone()
            if not photo:
                skipped.append({"photo_id": photo_id, "reason": "not_found"})
                continue
            if photo["user_id"] != user_id:
                skipped.append({"photo_id": photo_id, "reason": "not_owned"})
                continue
            # Check already associated (silently skip)
            existing = db.execute(
                "SELECT id FROM album_photos WHERE album_id = ? AND photo_id = ?",
                (album_id, photo_id),
            ).fetchone()
            if existing:
                continue
            db.execute(
                "INSERT INTO album_photos (album_id, photo_id) VALUES (?, ?)",
                (album_id, photo_id),
            )
            associated_count += 1

    return {"associated_count": associated_count, "skipped": skipped}


def remove_photo_from_album(
    user_id: int,
    event_id: int,
    album_id: int,
    photo_id: int,
) -> bool | None:
    with connection() as db:
        if not _album_owned(db, user_id, event_id, album_id):
            return None
        cursor = db.execute(
            "DELETE FROM album_photos WHERE album_id = ? AND photo_id = ?",
            (album_id, photo_id),
        )
        return cursor.rowcount > 0
