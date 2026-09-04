import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import { authHeaders } from "../services/auth";

export default function Events() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", event_date: "", description: "" });
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: "", event_date: "", description: "" });
  const [editError, setEditError] = useState("");
  const [editSubmitting, setEditSubmitting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    API.get("/events", { headers: authHeaders() })
      .then(({ data }) => setEvents(data.events || []))
      .catch(() => setError("Could not load events. Please try again."))
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setFormError("");
    setSubmitting(true);
    try {
      const { data } = await API.post("/events", form, { headers: authHeaders() });
      setEvents((prev) => [data, ...prev]);
      setForm({ name: "", event_date: "", description: "" });
      setShowForm(false);
    } catch (err) {
      setFormError(err.response?.data?.detail || "Could not create event. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this event? All albums and photo associations will be removed.")) return;
    try {
      await API.delete(`/events/${id}`, { headers: authHeaders() });
      setEvents((prev) => prev.filter((ev) => ev.id !== id));
    } catch {
      setError("Could not delete event. Please try again.");
    }
  };

  const startEdit = (ev, e) => {
    e.stopPropagation();
    setEditingId(ev.id);
    setEditForm({ name: ev.name, event_date: ev.event_date, description: ev.description || "" });
    setEditError("");
  };

  const handleEdit = async (e, id) => {
    e.preventDefault();
    setEditSubmitting(true);
    setEditError("");
    try {
      const { data } = await API.put(`/events/${id}`, editForm, { headers: authHeaders() });
      setEvents((prev) => prev.map((ev) => ev.id === id ? { ...ev, ...data } : ev));
      setEditingId(null);
    } catch (err) {
      setEditError(err.response?.data?.detail || "Could not update event.");
    } finally {
      setEditSubmitting(false);
    }
  };

  return (
    <main className="content-shell">
      <section className="page-card">
        <div className="page-heading">
          <div>
            <p className="eyebrow">MY EVENTS</p>
            <h1>Events</h1>
            <p className="muted">Organise your photos into events and albums.</p>
          </div>
          <button className="primary-button" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Cancel" : "+ New Event"}
          </button>
        </div>

        {showForm && (
          <form className="inline-form" onSubmit={handleCreate}>
            <label>
              Event name *
              <input
                required
                maxLength={200}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. College Farewell Party"
              />
            </label>
            <label>
              Date *
              <input
                type="date"
                required
                value={form.event_date}
                onChange={(e) => setForm({ ...form, event_date: e.target.value })}
              />
            </label>
            <label>
              Description
              <textarea
                maxLength={1000}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Optional description"
              />
            </label>
            {formError && <p className="form-error">{formError}</p>}
            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? "Creating…" : "Create Event"}
            </button>
          </form>
        )}

        {error && <p className="form-error">{error}</p>}

        {loading ? (
          <p className="muted">Loading…</p>
        ) : events.length === 0 ? (
          <div className="empty-state">
            <p>No events yet.</p>
            <button className="secondary-button" onClick={() => setShowForm(true)}>Create your first event</button>
          </div>
        ) : (
          <div className="card-grid">
            {events.map((ev) => (
              <div key={ev.id} className="event-card">
                {editingId === ev.id ? (
                  <form className="inline-form" onSubmit={(e) => handleEdit(e, ev.id)} onClick={(e) => e.stopPropagation()}>
                    <label>Name *<input required maxLength={200} value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} /></label>
                    <label>Date *<input type="date" required value={editForm.event_date} onChange={(e) => setEditForm({ ...editForm, event_date: e.target.value })} /></label>
                    <label>Description<textarea maxLength={1000} value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} /></label>
                    {editError && <p className="form-error">{editError}</p>}
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <button className="primary-button" type="submit" disabled={editSubmitting}>{editSubmitting ? "Saving…" : "Save"}</button>
                      <button className="secondary-button" type="button" onClick={() => setEditingId(null)}>Cancel</button>
                    </div>
                  </form>
                ) : (
                  <>
                    <div className="event-card-body" onClick={() => navigate(`/events/${ev.id}`)} style={{ cursor: "pointer" }}>
                      <h3>{ev.name}</h3>
                      <p className="muted">{ev.event_date}</p>
                      {ev.album_count !== undefined && (
                        <span className="badge">{ev.album_count} album{ev.album_count !== 1 ? "s" : ""}</span>
                      )}
                      {ev.description && <p className="muted small">{ev.description}</p>}
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", padding: "0.5rem 0 0" }}>
                      <button className="secondary-button" style={{ fontSize: "0.8rem" }} onClick={(e) => startEdit(ev, e)}>Edit</button>
                      <button className="danger-button" onClick={(e) => { e.stopPropagation(); handleDelete(ev.id); }}>Delete</button>
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
