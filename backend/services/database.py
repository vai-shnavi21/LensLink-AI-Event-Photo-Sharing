import os
DATABASE_URL = os.getenv("DATABASE_URL")


class PostgresConnection:
    """Compatibility wrapper for the existing SQLite-style query calls."""

    def __init__(self):
        import psycopg
        from psycopg.rows import dict_row

        self._connection = psycopg.connect(DATABASE_URL, row_factory=dict_row)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self._connection.commit()
        else:
            self._connection.rollback()
        self._connection.close()

    def execute(self, query, parameters=()):
        # Existing routes use SQLite's ? placeholders; psycopg uses %s.
        return self._connection.execute(query.replace("?", "%s"), parameters)

def connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required. Configure PostgreSQL; SQLite is not used by this application.")
    return PostgresConnection()

def setup_database():
    if DATABASE_URL:
        with connection() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    full_name TEXT NOT NULL,
                    avatar_url TEXT,
                    google_id TEXT UNIQUE,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS gallery_photos (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id),
                    public_id TEXT NOT NULL,
                    image_url TEXT NOT NULL,
                    thumbnail_url TEXT,
                    title TEXT NOT NULL,
                    album_only BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Existing deployments may have been created before album_only was
            # introduced.  Keep startup migrations safe and idempotent.
            db.execute("""
                ALTER TABLE gallery_photos
                ADD COLUMN IF NOT EXISTS album_only BOOLEAN NOT NULL DEFAULT FALSE
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS face_embeddings (
                    id BIGSERIAL PRIMARY KEY,
                    owner_user_id BIGINT NOT NULL REFERENCES users(id),
                    source_url TEXT NOT NULL,
                    face_index INTEGER NOT NULL,
                    embedding JSONB NOT NULL,
                    bounding_box JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (owner_user_id, source_url, face_index)
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id          BIGSERIAL PRIMARY KEY,
                    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name        TEXT NOT NULL,
                    event_date  DATE NOT NULL,
                    description TEXT,
                    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS albums (
                    id          BIGSERIAL PRIMARY KEY,
                    event_id    BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                    name        TEXT NOT NULL,
                    description TEXT,
                    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS album_photos (
                    id          BIGSERIAL PRIMARY KEY,
                    album_id    BIGINT NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
                    photo_id    BIGINT NOT NULL REFERENCES gallery_photos(id) ON DELETE CASCADE,
                    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (album_id, photo_id)
                )
            """)
