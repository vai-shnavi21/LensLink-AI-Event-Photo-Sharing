import React, { useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import API from "../services/api";
import { authHeaders } from "../services/auth";

export default function EventDetail() {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", description: "" });
  const [submitting, setSubmitting] = useState(false);

  const [editingAlbumId, setEditingAlbumId] = useState(null);
  const [editAlbumForm, setEditAlbumForm] = useState({ name: "", description: "" });
  const [editAlbumError, setEditAlbumError] = useState("");
  const [editAlbumSubmitting, setEditAlbumSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([
      API.get(`/events/${eventId}`, { headers: authHeaders() }),
      API.get(`/events/${eventId}/albums`, { headers: authHeaders() }),
    ])
      .then(([evRes, alRes]) => {
        setEvent(evRes.data);
        setAlbums(alRes.data.albums || []);
      })
      .catch(() => setError("Could not load event details."))
      .finally(() => setLoading(false));
  }, [eventId]);

  const handleCreateAlbum = async (e) => {
    e.preventDefault();
    setFormError("");
    setSubmitting(true);
    try {
      const { data } = await API.post(`/events/${eventId}/albums`, form, { headers: authHeaders() });
      setAlbums((prev) => [...prev, data]);
      setForm({ name: "", description: "" });
      setShowForm(false);
    } catch (err) {
      setFormError(err.response?.data?.detail || "Could not create album.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteAlbum = async (albumId) => {
    if (!window.confirm("Delete this album? Photos will remain in your gallery.")) return;
    try {
      await API.delete(`/events/${eventId}/albums/${albumId}`, { headers: authHeaders() });
      setAlbums((prev) => prev.filter((a) => a.id !== albumId));
    } catch {
      setError("Could not delete album.");
    }
  };

  const startEditAlbum = (al, e) => {
    e.stopPropagation();
    setEditingAlbumId(al.id);
    setEditAlbumForm({ name: al.name, description: al.description || "" });
    setEditAlbumError("");
  };

  const handleEditAlbum = async (e, albumId) => {
    e.preventDefault();
    setEditAlbumSubmitting(true);
    setEditAlbumError("");
    try {
      const { data } = await API.put(`/events/${eventId}/albums/${albumId}`, editAlbumForm, { headers: authHeaders() });
      setAlbums((prev) => prev.map((a) => a.id === albumId ? { ...a, ...data } : a));
      setEditingAlbumId(null);
    } catch (err) {
      setEditAlbumError(err.response?.data?.detail || "Could not update album.");
    } finally {
      setEditAlbumSubmitting(false);
    }
  };

  if (loading) return <main className="content-shell"><p className="muted">Loading…</p></main>;
  if (!event) return <main className="content-shell"><p className="form-error">{error || "Event not found."}</p></main>;

  return (
    <main className="content-shell">
      <section className="page-card">
        <p className="muted"><Link to="/events">← Events</Link></p>
        <div className="page-heading">
          <div>
            <p className="eyebrow">EVENT</p>
            <h1>{event.name}</h1>
            <p className="muted">{event.event_date}</p>
            {event.description && <p>{event.description}</p>}
          </div>
          <button className="primary-button" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Cancel" : "+ New Album"}
          </button>
        </div>

        {showForm && (
          <form className="inline-form" onSubmit={handleCreateAlbum}>
            <label>
              Album name *
              <input
                required
                maxLength={200}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. Stage Performances"
              />
            </label>
            <label>
              Description
              <textarea
                maxLength={500}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Optional"
              />
            </label>
            {formError && <p className="form-error">{formError}</p>}
            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? "Creating…" : "Create Album"}
            </button>
          </form>
        )}

        {error && <p className="form-error">{error}</p>}

        {albums.length === 0 ? (
          <div className="empty-state">
            <p>No albums yet.</p>
            <button className="secondary-button" onClick={() => setShowForm(true)}>Create your first album</button>
          </div>
        ) : (
          <div className="card-grid">
            {albums.map((al) => (
              <div key={al.id} className="event-card">
                {editingAlbumId === al.id ? (
                  <form className="inline-form" onSubmit={(e) => handleEditAlbum(e, al.id)} onClick={(e) => e.stopPropagation()}>
                    <label>Name *<input required maxLength={200} value={editAlbumForm.name} onChange={(e) => setEditAlbumForm({ ...editAlbumForm, name: e.target.value })} /></label>
                    <label>Description<textarea maxLength={500} value={editAlbumForm.description} onChange={(e) => setEditAlbumForm({ ...editAlbumForm, description: e.target.value })} /></label>
                    {editAlbumError && <p className="form-error">{editAlbumError}</p>}
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <button className="primary-button" type="submit" disabled={editAlbumSubmitting}>{editAlbumSubmitting ? "Saving…" : "Save"}</button>
                      <button className="secondary-button" type="button" onClick={() => setEditingAlbumId(null)}>Cancel</button>
                    </div>
                  </form>
                ) : (
                  <>
                    <div className="event-card-body" onClick={() => navigate(`/events/${eventId}/albums/${al.id}`)} style={{ cursor: "pointer" }}>
                      <h3>{al.name}</h3>
                      {al.description && <p className="muted small">{al.description}</p>}
                      <span className="badge">{al.photo_count || 0} photo{al.photo_count !== 1 ? "s" : ""}</span>
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", padding: "0.5rem 0 0" }}>
                      <button className="secondary-button" style={{ fontSize: "0.8rem" }} onClick={(e) => startEditAlbum(al, e)}>Edit</button>
                      <button className="danger-button" onClick={(e) => { e.stopPropagation(); handleDeleteAlbum(al.id); }}>Delete</button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
