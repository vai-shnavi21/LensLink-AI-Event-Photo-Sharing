import React, { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import API from "../services/api";
import { authHeaders } from "../services/auth";

export default function AlbumDetail() {
  const { eventId, albumId } = useParams();
  const [photos, setPhotos] = useState([]);
  const [galleryPhotos, setGalleryPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showMapPicker, setShowMapPicker] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [mapping, setMapping] = useState(false);
  const uploadRef = useRef();

  useEffect(() => {
    API.get(`/events/${eventId}/albums/${albumId}/photos`, { headers: authHeaders() })
      .then(({ data }) => setPhotos(data.photos || []))
      .catch(() => setError("Could not load album photos."))
      .finally(() => setLoading(false));
  }, [eventId, albumId]);

  const handleUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    setUploading(true);
    setError("");
    try {
      const formData = new FormData();
      files.forEach((f) => formData.append("files", f));
      const { data } = await API.post(
        `/events/${eventId}/albums/${albumId}/photos/upload`,
        formData,
        { headers: { ...authHeaders() } }
      );
      setPhotos((prev) => [...prev, ...(data.photos || [])]);
      if (data.indexing?.status === "failed") {
        setError(`Photos uploaded, but face scanning failed: ${data.indexing.message}`);
      } else if (data.indexing?.status === "no_faces_detected") {
        setError("Photos uploaded, but no faces were detected in them.");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
      if (uploadRef.current) uploadRef.current.value = "";
    }
  };

  const openMapPicker = async () => {
    try {
      const { data } = await API.get("/gallery", { headers: authHeaders() });
      // Filter out photos already in this album
      const alreadyInAlbum = new Set(photos.map((p) => p.id));
      const available = (data.photos || []).filter((p) => !alreadyInAlbum.has(p.id));
      setGalleryPhotos(available);
      setSelectedIds([]);
      setShowMapPicker(true);
    } catch {
      setError("Could not load gallery photos.");
    }
  };

  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleMap = async () => {
    if (!selectedIds.length) return;
    setMapping(true);
    setError("");
    try {
      const { data } = await API.post(
        `/events/${eventId}/albums/${albumId}/photos/map`,
        { photo_ids: selectedIds },
        { headers: authHeaders() }
      );
      // Reload photos after mapping
      const { data: fresh } = await API.get(
        `/events/${eventId}/albums/${albumId}/photos`,
        { headers: authHeaders() }
      );
      setPhotos(fresh.photos || []);
      setShowMapPicker(false);
      if (data.skipped?.length) {
        setError(`${data.associated_count} photo(s) added. ${data.skipped.length} skipped.`);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Could not map photos.");
    } finally {
      setMapping(false);
    }
  };

  const handleRemove = async (photoId) => {
    if (!window.confirm("Remove this photo from the album? It will stay in your gallery.")) return;
    try {
      await API.delete(`/events/${eventId}/albums/${albumId}/photos/${photoId}`, { headers: authHeaders() });
      setPhotos((prev) => prev.filter((p) => p.id !== photoId));
    } catch {
      setError("Could not remove photo.");
    }
  };

  return (
    <main className="content-shell">
      <section className="page-card">
        <p className="muted"><Link to={`/events/${eventId}`}>← Back to Event</Link></p>
        <div className="page-heading">
          <div>
            <p className="eyebrow">ALBUM</p>
            <h1>Album Photos</h1>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <label className="secondary-button" style={{ cursor: "pointer" }}>
              {uploading ? "Uploading…" : "Upload Photos"}
              <input
                ref={uploadRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif"
                multiple
                style={{ display: "none" }}
                onChange={handleUpload}
                disabled={uploading}
              />
            </label>
            <button className="secondary-button" onClick={openMapPicker}>Map from Gallery</button>
          </div>
        </div>

        {error && <p className="form-error">{error}</p>}

        {loading ? (
          <p className="muted">Loading…</p>
        ) : photos.length === 0 ? (
          <div className="empty-state">
            <p>No photos in this album yet.</p>
            <p className="muted">Upload photos or map them from your gallery.</p>
          </div>
        ) : (
          <div className="photo-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem" }}>
            {photos.map((photo) => (
              <div key={photo.id} style={{ position: "relative" }}>
                <img
                  src={photo.thumbnail_url || photo.image_url}
                  alt={photo.title || "Album photo"}
                  style={{ width: "100%", borderRadius: "8px", display: "block", aspectRatio: "1", objectFit: "cover" }}
                />
                <button
                  className="danger-button"
                  style={{ position: "absolute", top: "4px", right: "4px", fontSize: "0.7rem", padding: "2px 6px" }}
                  onClick={() => handleRemove(photo.id)}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Map from gallery picker */}
        {showMapPicker && (
          <div className="modal" role="dialog" aria-modal="true" aria-label="Map gallery photos">
            <div className="camera-modal" style={{ maxWidth: "600px", maxHeight: "80vh", overflowY: "auto" }}>
              <button className="close-button" onClick={() => setShowMapPicker(false)} aria-label="Close">×</button>
              <h2>Select Gallery Photos</h2>
              <p className="muted">Click photos to select them, then click Add Selected.</p>
              {galleryPhotos.length === 0 ? (
                <p className="muted">No gallery photos to add. Upload photos in My Gallery first, or all your photos are already in this album.</p>
              ) : (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))", gap: "0.5rem", margin: "1rem 0" }}>
                  {galleryPhotos.map((p) => (
                    <div
                      key={p.id}
                      onClick={() => toggleSelect(p.id)}
                      style={{
                        cursor: "pointer",
                        border: selectedIds.includes(p.id) ? "3px solid #6c47ff" : "3px solid transparent",
                        borderRadius: "6px",
                        overflow: "hidden",
                      }}
                    >
                      <img
                        src={p.thumbnail_url || p.image_url}
                        alt={p.title}
                        style={{ width: "100%", aspectRatio: "1", objectFit: "cover", display: "block" }}
                      />
                    </div>
                  ))}
                </div>
              )}
              <div className="camera-actions">
                <button className="secondary-button" onClick={() => setShowMapPicker(false)}>Cancel</button>
                <button className="primary-button" onClick={handleMap} disabled={mapping || !selectedIds.length}>
                  {mapping ? "Adding…" : `Add Selected (${selectedIds.length})`}
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
