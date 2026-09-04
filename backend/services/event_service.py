from services.database import connection


def create_event(user_id: int, name: str, event_date: str, description: str | None) -> dict:
    """
    Insert a new event row and return it as a dict.
    event_date is accepted as a YYYY-MM-DD string and returned the same way.
    """
    with connection() as db:
        cursor = db.execute(
            """
            INSERT INTO events (user_id, name, event_date, description)
            VALUES (?, ?, ?, ?)
            RETURNING id, user_id, TO_CHAR(event_date, 'YYYY-MM-DD') AS event_date,
                      name, description, created_at
            """,
            (user_id, name, event_date, description),
        )
        row = cursor.fetchone()
    return dict(row)


def list_events(user_id: int) -> list[dict]:
    """
    Return all events owned by user_id, newest event_date first.
    """
    with connection() as db:
        cursor = db.execute(
            """
            SELECT id, user_id, name,
                   TO_CHAR(event_date, 'YYYY-MM-DD') AS event_date,
                   description, created_at
            FROM events
            WHERE user_id = ?
            ORDER BY event_date DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_event(user_id: int, event_id: int) -> dict | None:
    """
    Return a single event with its album_count.
    Ownership is enforced: returns None if the event doesn't exist or
    belongs to a different user.
    """
    with connection() as db:
        cursor = db.execute(
            """
            SELECT events.id,
                   events.user_id,
                   events.name,
                   TO_CHAR(events.event_date, 'YYYY-MM-DD') AS event_date,
                   events.description,
                   events.created_at,
                   COUNT(albums.id) AS album_count
            FROM events
            LEFT JOIN albums ON albums.event_id = events.id
            WHERE events.id = ?
              AND events.user_id = ?
            GROUP BY events.id
            """,
            (event_id, user_id),
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return dict(row)


def update_event(
    user_id: int,
    event_id: int,
    name: str | None = None,
    event_date: str | None = None,
    description: str | None = None,
) -> dict | None:
    """
    Update only the provided (non-None) fields of an event.
    Ownership is enforced via WHERE id = ? AND user_id = ?.
    Returns the updated row as a dict, or None if not found / not owned.
    """
    fields = []
    values = []

    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if event_date is not None:
        fields.append("event_date = ?")
        values.append(event_date)
    if description is not None:
        fields.append("description = ?")
        values.append(description)

    # Caller guarantees at least one field is non-None, but guard anyway.
    if not fields:
        return None

    set_clause = ", ".join(fields)
    values.extend([event_id, user_id])

    with connection() as db:
        cursor = db.execute(
            f"""
            UPDATE events
            SET {set_clause}
            WHERE id = ? AND user_id = ?
            RETURNING id, user_id, name,
                      TO_CHAR(event_date, 'YYYY-MM-DD') AS event_date,
                      description, created_at
            """,
            tuple(values),
        )
        row = cursor.fetchone()

    if row is None:
        return None
    return dict(row)


def delete_event(user_id: int, event_id: int) -> bool:
    """
    Delete an event owned by user_id.
    Returns True if the row was deleted, False if not found or not owned.
    CASCADE in the schema automatically removes related albums and album_photos.
    """
    with connection() as db:
        cursor = db.execute(
            "DELETE FROM events WHERE id = ? AND user_id = ?",
            (event_id, user_id),
        )
        return cursor.rowcount > 0
