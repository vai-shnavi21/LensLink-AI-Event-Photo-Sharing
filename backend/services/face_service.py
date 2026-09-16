

# import os
# import cv2
# import json
# import numpy as np
# from tqdm import tqdm
# from concurrent.futures import ThreadPoolExecutor
# from insightface.app import FaceAnalysis
# import requests
# from io import BytesIO


# # Project Paths


# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DATA_DIR = os.getenv("APP_DATA_DIR", BASE_DIR)

# UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
# EVENT_FOLDER = os.path.join(UPLOAD_FOLDER, "event_photos")
# SELFIE_FOLDER = os.path.join(UPLOAD_FOLDER, "selfie")

# EMBEDDING_FOLDER = os.path.join(DATA_DIR, "embeddings")

# EMBEDDING_PATH = os.path.join(EMBEDDING_FOLDER, "embeddings.npy")
# MAPPING_PATH = os.path.join(EMBEDDING_FOLDER, "photo_mapping.json")

# os.makedirs(EVENT_FOLDER, exist_ok=True)
# os.makedirs(SELFIE_FOLDER, exist_ok=True)
# os.makedirs(EMBEDDING_FOLDER, exist_ok=True)


# DETECTION_MAX_DIM = 1280


# # Load InsightFace Model


# def get_ctx_id():
#     """Use GPU if a CUDA execution provider is actually available, else CPU."""
#     try:
#         import onnxruntime as ort
#         providers = ort.get_available_providers()
#         if "CUDAExecutionProvider" in providers:
#             return 0
#     except Exception:
#         pass
#     return -1


# CTX_ID = get_ctx_id()

# app = FaceAnalysis(name="buffalo_l")

# #LARGE DATAsET

# app.prepare(
#     ctx_id=CTX_ID,
#     det_size=(320, 320)
# )

# # SINGLE PHOTO
# selfie_app = FaceAnalysis(name="buffalo_l")
# selfie_app.prepare(
#     ctx_id=CTX_ID,
#     det_size=(640, 640)
# )

# print("InsightFace Models Loaded Successfully")
# print("Using:", "GPU" if CTX_ID == 0 else "CPU")


# # Helpers


# def resize_for_detection(image, max_dim=DETECTION_MAX_DIM):
#     h, w = image.shape[:2]
#     scale = max_dim / max(h, w)
#     if scale < 1:
#         image = cv2.resize(image, (int(w * scale), int(h * scale)))
#     return image


# def download_image_from_url(url: str):
#     """
#     Download image from cloud URL and return as numpy array
    
#     Args:
#         url: Cloud URL of the image
    
#     Returns:
#         tuple: (filename, image_array) or (filename, None) if failed
#     """
#     try:
#         response = requests.get(url, timeout=10)
#         response.raise_for_status()
        
#         # Convert bytes to image
#         nparr = np.frombuffer(response.content, np.uint8)
#         image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
#         # Extract filename from URL
#         filename = url.split("/")[-1].split("?")[0] or "cloud_image"
        
#         return filename, image
#     except Exception as e:
#         print(f"Error downloading image from {url}: {str(e)}")
#         return url.split("/")[-1], None


# def read_image(photo):
#     """
#     Read image from local file
    
#     Args:
#         photo: Filename of local photo
    
#     Returns:
#         tuple: (filename, image_array)
#     """
#     path = os.path.join(EVENT_FOLDER, photo)
#     image = cv2.imread(path)
#     return photo, image


# def read_image_from_cloud(cloud_url: str):
#     """
#     Read image from cloud URL
    
#     Args:
#         cloud_url: Cloud URL of the photo
    
#     Returns:
#         tuple: (url, image_array)
#     """
#     _, image = download_image_from_url(cloud_url)
#     # Persist the Cloudinary URL in the face mapping for matching results.
#     return cloud_url, image


# def load_existing_mapping():
#     if not os.path.exists(MAPPING_PATH):
#         return []
#     with open(MAPPING_PATH, "r") as f:
#         return json.load(f)


# def load_existing_embeddings():
#     if not os.path.exists(EMBEDDING_PATH):
#         return None
#     return np.load(EMBEDDING_PATH).astype("float32")


# # Process Event Photos


# def process_event_photos(force_reprocess=False):
#     """
#     Generates face embeddings for all event photos.
#     By default, skips photos already present in photo_mapping.json,
#     so re-running after new uploads only processes new photos.
#     """

#     existing_mapping = [] if force_reprocess else load_existing_mapping()
#     existing_embeddings = None if force_reprocess else load_existing_embeddings()

#     already_processed = {m["photo"] for m in existing_mapping}

#     all_photos = os.listdir(EVENT_FOLDER)
#     photos = [p for p in all_photos if p not in already_processed]

#     print(f"Total Photos Found : {len(all_photos)}")
#     print(f"Already Processed  : {len(already_processed)}")
#     print(f"New Photos To Process : {len(photos)}")

#     if len(photos) == 0:
#         print("Nothing new to process.")
#         return False

#     new_embeddings = []
#     new_photo_names = []
#     new_bounding_boxes = []

   
#     with ThreadPoolExecutor(max_workers=8) as executor:
#         loaded = list(tqdm(
#             executor.map(read_image, photos),
#             total=len(photos),
#             desc="Reading images"
#         ))

#     for photo, image in tqdm(loaded, desc="Detecting faces"):

#         if image is None:
#             print(f"Skipping (unreadable) {photo}")
#             continue

#         image = resize_for_detection(image)

#         faces = app.get(image)

#         if len(faces) == 0:
#             print(f"{photo} -> 0 face(s)")
#             continue

#         for face in faces:
#             new_embeddings.append(face.embedding)
#             new_photo_names.append(photo)
#             new_bounding_boxes.append(face.bbox.tolist())

#     if len(new_embeddings) == 0:
#         print("No new faces found.")
#         return False

#     new_embedding_array = np.array(new_embeddings).astype("float32")

    
#     if existing_embeddings is not None and existing_embeddings.shape[0] > 0:
#         embedding_array = np.vstack([existing_embeddings, new_embedding_array])
#     else:
#         embedding_array = new_embedding_array

#     np.save(EMBEDDING_PATH, embedding_array)

#     mapping = list(existing_mapping)
#     for i in range(len(new_photo_names)):
#         mapping.append({
#             "photo": new_photo_names[i],
#             "bbox": new_bounding_boxes[i]
#         })

#     with open(MAPPING_PATH, "w") as f:
#         json.dump(mapping, f, indent=4)

#     print("=" * 50)
#     print("Embedding Generation Completed")
#     print("=" * 50)
#     print("New Faces Indexed :", len(new_embeddings))
#     print("Total Faces Indexed :", len(mapping))

#     return True


# def process_cloud_event_photos(cloud_urls: list, force_reprocess=False):
#     """
#     Generates face embeddings for event photos from cloud URLs.
    
#     Args:
#         cloud_urls: List of cloud URLs to process
#         force_reprocess: Force reprocessing even if already processed
    
#     Returns:
#         bool: True if new embeddings were processed
#     """
#     existing_mapping = [] if force_reprocess else load_existing_mapping()
#     existing_embeddings = None if force_reprocess else load_existing_embeddings()

#     already_processed = {m["photo"] for m in existing_mapping}
#     urls_to_process = [url for url in cloud_urls if url not in already_processed]

#     print(f"Total Cloud Photos Found : {len(cloud_urls)}")
#     print(f"Already Processed  : {len(already_processed)}")
#     print(f"New Photos To Process : {len(urls_to_process)}")

#     if len(urls_to_process) == 0:
#         print("Nothing new to process.")
#         return False

#     new_embeddings = []
#     new_photo_names = []
#     new_bounding_boxes = []

#     with ThreadPoolExecutor(max_workers=4) as executor:
#         loaded = list(tqdm(
#             executor.map(read_image_from_cloud, urls_to_process),
#             total=len(urls_to_process),
#             desc="Downloading cloud images"
#         ))

#     for photo_name, image in tqdm(loaded, desc="Detecting faces"):
#         if image is None:
#             print(f"Skipping (unreadable) {photo_name}")
#             continue

#         image = resize_for_detection(image)
#         faces = app.get(image)

#         if len(faces) == 0:
#             print(f"{photo_name} -> 0 face(s)")
#             continue

#         for face in faces:
#             new_embeddings.append(face.embedding)
#             new_photo_names.append(photo_name)
#             new_bounding_boxes.append(face.bbox.tolist())

#     if len(new_embeddings) == 0:
#         print("No new faces found.")
#         return False

#     new_embedding_array = np.array(new_embeddings).astype("float32")

#     if existing_embeddings is not None and existing_embeddings.shape[0] > 0:
#         embedding_array = np.vstack([existing_embeddings, new_embedding_array])
#     else:
#         embedding_array = new_embedding_array

#     np.save(EMBEDDING_PATH, embedding_array)

#     mapping = list(existing_mapping)
#     for i in range(len(new_photo_names)):
#         mapping.append({
#             "photo": new_photo_names[i],
#             "bbox": new_bounding_boxes[i]
#         })

#     with open(MAPPING_PATH, "w") as f:
#         json.dump(mapping, f, indent=4)

#     print("=" * 50)
#     print("Embedding Generation Completed")
#     print("=" * 50)
#     print("New Faces Indexed :", len(new_embeddings))
#     print("Total Faces Indexed :", len(mapping))

#     return True



# # Generate Embedding for Selfie


# def generate_selfie_embedding(selfie_path):
#     """
#     Generate face embedding from local selfie file
    
#     Args:
#         selfie_path: Path to local selfie file
    
#     Returns:
#         numpy array: Face embedding or None if no face detected
#     """
#     image = cv2.imread(selfie_path)

#     if image is None:
#         return None

#     faces = selfie_app.get(image)

#     if len(faces) == 0:
#         return None

    
#     face = max(
#         faces,
#         key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
#     )

#     embedding = face.embedding.astype("float32")

#     return embedding


# def generate_selfie_embedding_from_cloud(cloud_url: str):
#     """
#     Generate face embedding from cloud selfie URL
    
#     Args:
#         cloud_url: Cloud URL of selfie image
    
#     Returns:
#         numpy array: Face embedding or None if no face detected
#     """
#     _, image = download_image_from_url(cloud_url)

#     if image is None:
#         return None

#     faces = selfie_app.get(image)

#     if len(faces) == 0:
#         return None

#     # Get the largest face (assumed to be the person's face)
#     face = max(
#         faces,
#         key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
#     )

#     embedding = face.embedding.astype("float32")

#     return embedding


# if __name__ == "__main__":
#     process_event_photos()











"""Face processing backed only by Cloudinary URLs and PostgreSQL."""

import json
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import requests
from insightface.app import FaceAnalysis

from services.database import connection


# Maximum image dimension used for face detection.
DETECTION_MAX_DIM = 800

# One shared InsightFace model.
# It is loaded only when face recognition is actually needed.
_model = None


def _get_model():
    """
    Load one shared InsightFace model.

    The same model is used for:
    - event photo face detection
    - selfie face detection

    This avoids loading two copies of buffalo_l into RAM.
    """

    global _model

    if _model is None:
        print("Loading InsightFace model...")

        _model = FaceAnalysis(
            name="buffalo_s",
            providers=["CPUExecutionProvider"],
        )

        # Use CPU because Render does not provide a GPU
        # on the free instance.
        _model.prepare(
            ctx_id=-1,
            det_size=(320, 320),
        )

        print("InsightFace model loaded.")

    return _model


def _image_from_url(url: str):
    """
    Download an image from Cloudinary and convert it
    into an OpenCV image.
    """

    try:
        response = requests.get(
            url,
            timeout=15,
        )

        response.raise_for_status()

        image = cv2.imdecode(
            np.frombuffer(
                response.content,
                np.uint8,
            ),
            cv2.IMREAD_COLOR,
        )

        return image

    except requests.RequestException as error:
        print(f"Failed to download image: {error}")
        return None


def _resize_for_detection(image):
    """
    Resize very large images before face detection.

    This reduces CPU and memory usage while keeping
    the original Cloudinary image URL unchanged.
    """

    if image is None:
        return None

    height, width = image.shape[:2]

    largest_dimension = max(
        height,
        width,
    )

    if largest_dimension <= DETECTION_MAX_DIM:
        return image

    scale = (
        DETECTION_MAX_DIM
        / largest_dimension
    )

    new_width = max(
        1,
        int(width * scale),
    )

    new_height = max(
        1,
        int(height * scale),
    )

    return cv2.resize(
        image,
        (new_width, new_height),
    )


def process_cloud_event_photos(
    cloud_urls: list[str],
    owner_user_id: int,
) -> bool:
    """
    Process uploaded event photos.

    For every Cloudinary image:
    1. Download the image.
    2. Detect all faces.
    3. Generate an embedding for each face.
    4. Store the embedding in PostgreSQL.

    Uses the shared InsightFace model.
    """

    if not cloud_urls:
        return False

    model = _get_model()

    records = []

    # Keep this at 2 instead of 4 to reduce memory usage.
    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        images = list(
            executor.map(
                _image_from_url,
                cloud_urls,
            )
        )

    downloaded_images = 0

    for url, image in zip(
        cloud_urls,
        images,
    ):

        if image is None:
            continue

        downloaded_images += 1

        try:
            # Record original dimensions before resizing so we can scale
            # bounding boxes back to original image coordinates.
            orig_h, orig_w = image.shape[:2]

            image = _resize_for_detection(image)

            # Compute the scale factor that was applied
            det_h, det_w = image.shape[:2]
            scale_x = orig_w / det_w if det_w > 0 else 1.0
            scale_y = orig_h / det_h if det_h > 0 else 1.0

            faces = model.get(image)

            for face_index, face in enumerate(
                faces
            ):

                embedding = (
                    face.embedding
                    .astype("float32")
                    .tolist()
                )

                # Scale bbox back to original image coordinates
                x1, y1, x2, y2 = face.bbox.astype("float32").tolist()
                bounding_box = [
                    x1 * scale_x,
                    y1 * scale_y,
                    x2 * scale_x,
                    y2 * scale_y,
                ]

                records.append(
                    (
                        owner_user_id,
                        url,
                        face_index,
                        json.dumps(
                            embedding
                        ),
                        json.dumps(
                            bounding_box
                        ),
                    )
                )

        finally:
            # Release the OpenCV image from memory.
            del image

    if downloaded_images == 0:
        raise RuntimeError("Could not download any uploaded photo for face indexing")

    if not records:
        return False

    # Store all face embeddings in PostgreSQL.
    with connection() as db:

        for record in records:

            db.execute(
                """
                INSERT INTO face_embeddings(
                    owner_user_id,
                    source_url,
                    face_index,
                    embedding,
                    bounding_box
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?::jsonb,
                    ?::jsonb
                )
                ON CONFLICT (
                    owner_user_id,
                    source_url,
                    face_index
                )
                DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    bounding_box = EXCLUDED.bounding_box
                """,
                record,
            )

    return True


def index_unprocessed_photos(owner_user_id: int, source_urls: list[str]) -> bool:
    """Index only photos that do not yet have a stored face embedding.

    This repairs photos uploaded before face indexing was connected to albums
    and avoids re-running recognition for photos that are already indexed.
    """
    urls = list(dict.fromkeys(url for url in source_urls if url))
    if not urls:
        return False

    placeholders = ",".join("?" for _ in urls)
    with connection() as db:
        rows = db.execute(
            f"""
            SELECT DISTINCT source_url
            FROM face_embeddings
            WHERE owner_user_id = ? AND source_url IN ({placeholders})
            """,
            (owner_user_id, *urls),
        ).fetchall()

    indexed_urls = {row["source_url"] for row in rows}
    pending_urls = [url for url in urls if url not in indexed_urls]
    if not pending_urls:
        return False

    return process_cloud_event_photos(pending_urls, owner_user_id)


def generate_selfie_embedding_from_cloud(
    cloud_url: str,
):
    """
    Generate an embedding from a user's selfie.

    The same shared InsightFace model is used here.
    Only the largest detected face is selected.
    """

    model = _get_model()

    image = _image_from_url(
        cloud_url
    )

    if image is None:
        return None

    try:
        image = _resize_for_detection(
            image
        )

        faces = model.get(image)

        if not faces:
            return None

        # Select the largest detected face.
        largest_face = max(
            faces,
            key=lambda face: (
                (face.bbox[2] - face.bbox[0])
                * (face.bbox[3] - face.bbox[1])
            ),
        )

        return (
            largest_face.embedding
            .astype("float32")
        )

    finally:
        # Release image memory.
        del image


def search_faces(
    query_embedding,
    threshold: float = 0.60,
    top_k: int = 50,
    owner_user_id: int | None = None,
    search_scope: str = "gallery",
    scope_id: int | None = None,
) -> list[dict]:
    """
    Compare a selfie embedding against embeddings stored in PostgreSQL.
    Supports gallery / event / album scopes for filtered searches.
    """

    query = np.asarray(query_embedding, dtype="float32")
    query_norm = np.linalg.norm(query)
    if query_norm == 0:
        return []

    with connection() as db:
        if owner_user_id is None:
            # Legacy callers — no ownership filter
            rows = db.execute(
                "SELECT source_url, embedding FROM face_embeddings"
            ).fetchall()
        elif search_scope == "event" and scope_id is not None:
            rows = db.execute(
                """
                SELECT DISTINCT fe.source_url, fe.embedding
                FROM face_embeddings fe
                JOIN gallery_photos gp ON gp.image_url = fe.source_url
                JOIN album_photos ap ON ap.photo_id = gp.id
                JOIN albums al ON al.id = ap.album_id
                JOIN events ev ON ev.id = al.event_id
                WHERE fe.owner_user_id = ?
                  AND ev.id = ?
                  AND ev.user_id = ?
                """,
                (owner_user_id, scope_id, owner_user_id),
            ).fetchall()
        elif search_scope == "album" and scope_id is not None:
            rows = db.execute(
                """
                SELECT DISTINCT fe.source_url, fe.embedding
                FROM face_embeddings fe
                JOIN gallery_photos gp ON gp.image_url = fe.source_url
                JOIN album_photos ap ON ap.photo_id = gp.id
                JOIN albums al ON al.id = ap.album_id
                JOIN events ev ON ev.id = al.event_id
                WHERE fe.owner_user_id = ?
                  AND ap.album_id = ?
                  AND ev.user_id = ?
                """,
                (owner_user_id, scope_id, owner_user_id),
            ).fetchall()
        else:
            # gallery scope (default)
            rows = db.execute(
                "SELECT source_url, embedding FROM face_embeddings WHERE owner_user_id = ?",
                (owner_user_id,),
            ).fetchall()

    best_by_photo: dict[str, float] = {}

    for row in rows:
        raw = row["embedding"]
        embedding_data = json.loads(raw) if isinstance(raw, str) else raw
        vector = np.asarray(embedding_data, dtype="float32")
        vector_norm = np.linalg.norm(vector)
        denom = query_norm * vector_norm
        if denom == 0:
            continue
        score = float(np.dot(query, vector) / denom)
        if score >= threshold:
            url = row["source_url"]
            best_by_photo[url] = max(score, best_by_photo.get(url, -1.0))

    return [
        {"image_url": url, "similarity_score": round(score, 3)}
        for url, score in sorted(best_by_photo.items(), key=lambda x: x[1], reverse=True)[:top_k]
    ]


def search_faces_multi(
    selfie_embeddings: list,
    threshold: float = 0.60,
    top_k: int = 50,
    owner_user_id: int | None = None,
    search_scope: str = "gallery",
    scope_id: int | None = None,
) -> tuple[list[dict], list[str | None]]:
    """
    Run search_faces for each embedding in the batch.
    Aggregate results, deduplicate by URL keeping highest score.
    Returns (aggregated_results, per_selfie_errors).
    """
    per_selfie_errors: list[str | None] = []
    aggregated: dict[str, float] = {}

    for embedding in selfie_embeddings:
        if embedding is None:
            per_selfie_errors.append("No face detected in selfie")
            continue
        per_selfie_errors.append(None)
        results = search_faces(
            embedding,
            threshold=threshold,
            top_k=top_k,
            owner_user_id=owner_user_id,
            search_scope=search_scope,
            scope_id=scope_id,
        )
        for item in results:
            url = item["image_url"]
            aggregated[url] = max(item["similarity_score"], aggregated.get(url, -1.0))

    merged = [
        {"image_url": url, "similarity_score": round(score, 3)}
        for url, score in sorted(aggregated.items(), key=lambda x: x[1], reverse=True)[:top_k]
    ]
    return merged, per_selfie_errors
