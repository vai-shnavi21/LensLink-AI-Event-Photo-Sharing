import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import API from "../services/api";
import { authHeaders } from "../services/auth";

export default function PersonDetail() {
  const { clusterId } = useParams();
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    API.get(`/people/clusters/${clusterId}/photos`, { headers: authHeaders() })
      .then(({ data }) => setPhotos(data.photos || []))
      .catch((err) => {
        const msg = err.response?.status === 404
          ? "Person not found."
          : "Could not load photos. Please try again.";
        setError(msg);
      })
      .finally(() => setLoading(false));
  };

  // useEffect(() => { load(); }, [clusterId]);
 // eslint-disable-next-line react-hooks/exhaustive-deps
useEffect(() => { load(); }, [clusterId]);
  return (
    <main className="content-shell">
      <section className="page-card">
        <p className="muted" style={{ marginBottom: "1rem" }}>
          <Link to="/people">← Back to People</Link>
        </p>

        <div className="page-heading">
          <div>
            <p className="eyebrow">PERSON</p>
            <h1>Photos of this person</h1>
            {!loading && !error && (
              <p className="muted">{photos.length} photo{photos.length !== 1 ? "s" : ""} found</p>
            )}
          </div>
        </div>

        {loading && <p className="muted">Loading photos…</p>}

        {error && (
          <div>
            <p className="form-error">{error}</p>
            <button className="secondary-button" onClick={load}>Retry</button>
          </div>
        )}

        {!loading && !error && photos.length === 0 && (
          <div className="empty-state">
            <p>No photos found for this person.</p>
          </div>
        )}

        {!loading && !error && photos.length > 0 && (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: "1rem",
            marginTop: "1.5rem",
          }}>
            {photos.map((photo) => (
              <div key={photo.id} style={{ borderRadius: "10px", overflow: "hidden", boxShadow: "0 2px 10px rgba(0,0,0,0.08)" }}>
                <a href={photo.image_url} target="_blank" rel="noopener noreferrer">
                  <img
                    src={photo.thumbnail_url || photo.image_url}
                    alt={photo.title || "Photo"}
                    style={{ width: "100%", aspectRatio: "1", objectFit: "cover", display: "block" }}
                  />
                </a>
                {photo.title && (
                  <div style={{ padding: "0.4rem 0.6rem", background: "#fff" }}>
                    <p style={{ margin: 0, fontSize: "0.8rem", color: "#555", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {photo.title}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
