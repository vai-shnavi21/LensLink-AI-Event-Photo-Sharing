import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import { authHeaders } from "../services/auth";

export default function People() {
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const load = () => {
    setLoading(true);
    setError("");
    API.get("/people/clusters", { headers: authHeaders() })
      .then(({ data }) => setClusters(data))
      .catch(() => setError("Could not load people. Please try again."))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <main className="content-shell">
      <section className="page-card">
        <div className="page-heading">
          <div>
            <p className="eyebrow">PEOPLE</p>
            <h1>People in your photos</h1>
            <p className="muted">Unique faces found across your gallery. Click a face to see all photos of that person.</p>
          </div>
        </div>

        {loading && <p className="muted">Detecting and grouping faces…</p>}

        {error && (
          <div>
            <p className="form-error">{error}</p>
            <button className="secondary-button" onClick={load}>Retry</button>
          </div>
        )}

        {!loading && !error && clusters.length === 0 && (
          <div className="empty-state">
            <p style={{ fontSize: "2rem" }}>👤</p>
            <p>No faces detected in your gallery yet.</p>
            <p className="muted">Upload some event photos first, then come back here.</p>
          </div>
        )}

        {!loading && clusters.length > 0 && (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
            gap: "1.25rem",
            marginTop: "1.5rem",
          }}>
            {clusters.map((cluster) => (
              <div
                key={cluster.cluster_id}
                onClick={() => navigate(`/people/${cluster.cluster_id}`)}
                style={{
                  cursor: "pointer",
                  textAlign: "center",
                  borderRadius: "12px",
                  overflow: "hidden",
                  boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
                  transition: "transform 0.15s, box-shadow 0.15s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "translateY(-3px)";
                  e.currentTarget.style.boxShadow = "0 6px 20px rgba(0,0,0,0.14)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "0 2px 12px rgba(0,0,0,0.08)";
                }}
              >
                <img
                  src={cluster.face_thumbnail_url}
                  alt="Person face"
                  style={{
                    width: "100%",
                    aspectRatio: "1",
                    objectFit: "cover",
                    display: "block",
                    backgroundColor: "#f0f0f0",
                  }}
                  onError={(e) => {
                    // Fallback if Cloudinary transform fails
                    e.target.style.display = "none";
                    e.target.parentNode.style.background = "#e8e8e8";
                  }}
                />
                <div style={{ padding: "0.5rem", background: "#fff" }}>
                  <p style={{ margin: 0, fontSize: "0.85rem", fontWeight: 600, color: "#333" }}>
                    {cluster.photo_count} photo{cluster.photo_count !== 1 ? "s" : ""}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
