import React, { useEffect, useRef, useState } from "react";
import API from "../services/api";
import { useNavigate } from "react-router-dom";
import { authHeaders } from "../services/auth";

export default function UploadSelfie() {
  const [selfies, setSelfies] = useState([]);         // array of {file, preview}
  const [cameraOpen, setCameraOpen] = useState(false);
  const [error, setError] = useState("");
  const [searching, setSearching] = useState(false);

  // Scope selector
  const [scope, setScope] = useState("gallery");
  const [events, setEvents] = useState([]);
  const [eventsError, setEventsError] = useState("");
  const [selectedEventId, setSelectedEventId] = useState("");
  const [albums, setAlbums] = useState([]);
  const [albumsError, setAlbumsError] = useState("");
  const [selectedAlbumId, setSelectedAlbumId] = useState("");

  const videoRef = useRef();
  const streamRef = useRef();
  const navigate = useNavigate();

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setCameraOpen(false);
  };

  useEffect(() => {
    if (cameraOpen && videoRef.current && streamRef.current)
      videoRef.current.srcObject = streamRef.current;
  }, [cameraOpen]);

  useEffect(() => () => { streamRef.current?.getTracks().forEach((t) => t.stop()); }, []);

  // Load events when scope changes to "event" or "album"
  useEffect(() => {
    if (scope === "event" || scope === "album") {
      setEventsError("");
      API.get("/events", { headers: authHeaders() })
        .then(({ data }) => setEvents(data.events || []))
        .catch(() => setEventsError("Could not load events"));
    }
  }, [scope]);

  // Load albums when event is selected and scope is "album"
  useEffect(() => {
    if (scope === "album" && selectedEventId) {
      setAlbumsError("");
      API.get(`/events/${selectedEventId}/albums`, { headers: authHeaders() })
        .then(({ data }) => setAlbums(data.albums || []))
        .catch(() => setAlbumsError("Could not load albums"));
    }
  }, [scope, selectedEventId]);

  const addFile = (file) => {
    if (!file) return;
    if (selfies.length >= 10) { setError("Maximum 10 selfies allowed."); return; }
    setSelfies((prev) => [...prev, { file, preview: URL.createObjectURL(file) }]);
    setError("");
  };

  const removeSelfie = (idx) => setSelfies((prev) => prev.filter((_, i) => i !== idx));

  const openCamera = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Camera not available in this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "user" } }, audio: false });
      streamRef.current = stream;
      setError("");
      setCameraOpen(true);
    } catch (err) {
      const msgs = {
        NotAllowedError: "Camera permission denied.",
        NotFoundError: "No camera found.",
        NotReadableError: "Camera in use by another app.",
      };
      setError(msgs[err.name] || "Camera could not start.");
    }
  };

  const capture = () => {
    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    if (!video?.videoWidth) { setError("Camera still starting. Try again."); return; }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob((blob) => { if (blob) addFile(new File([blob], "camera-selfie.jpg", { type: "image/jpeg" })); }, "image/jpeg", 0.92);
    stopCamera();
  };

  const searchPhotos = async () => {
    if (!selfies.length) { setError("Upload at least one selfie first."); return; }
    if (scope === "event" && !selectedEventId) {
      setError("Select an event before searching.");
      return;
    }
    if (scope === "album" && !selectedAlbumId) {
      setError("Select an album before searching.");
      return;
    }
    setSearching(true);
    setError("");

    const formData = new FormData();
    selfies.forEach(({ file }) => formData.append("files", file));
    formData.append("search_scope", scope);
    if (scope === "event" && selectedEventId) formData.append("scope_id", selectedEventId);
    if (scope === "album" && selectedAlbumId) formData.append("scope_id", selectedAlbumId);

    try {
      const response = await API.post("/search", formData, { headers: authHeaders() });
      navigate("/results", { state: { photos: response.data.matched_photos } });
    } catch (err) {
      setError(err.response?.data?.detail || "Search failed. Please try again.");
    } finally {
      setSearching(false);
    }
  };

  return (
    <main className="content-shell">
      <section className="page-card">
        <div className="page-heading">
          <div>
            <p className="eyebrow">SELFIE MATCH</p>
            <h1>Find your event photos</h1>
            <p className="muted">Upload up to 10 selfies to find photos of multiple people at once.</p>
          </div>
        </div>

        {/* Upload / camera buttons */}
        <div className="selfie-options">
          <label className="selfie-option">
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              onChange={(e) => Array.from(e.target.files).forEach(addFile)}
            />
            <span className="option-icon">↥</span>
            <strong>Upload selfies</strong>
            <small>Choose up to 10 photos</small>
          </label>
          <button type="button" className="selfie-option" onClick={openCamera}>
            <span className="option-icon">◉</span>
            <strong>Take a selfie</strong>
            <small>Use your device camera</small>
          </button>
        </div>

        {/* Selfie previews */}
        {selfies.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", margin: "1rem 0" }}>
            {selfies.map(({ preview }, idx) => (
              <div key={idx} style={{ position: "relative" }}>
                <img src={preview} alt={`Selfie ${idx + 1}`} style={{ width: 80, height: 80, objectFit: "cover", borderRadius: 8, display: "block" }} />
                <button
                  onClick={() => removeSelfie(idx)}
                  style={{ position: "absolute", top: -6, right: -6, background: "#e53e3e", color: "#fff", border: "none", borderRadius: "50%", width: 20, height: 20, cursor: "pointer", fontSize: 12, lineHeight: "20px", textAlign: "center" }}
                  aria-label="Remove selfie"
                >×</button>
              </div>
            ))}
          </div>
        )}

        {/* Scope selector */}
        <div style={{ margin: "1rem 0" }}>
          <label>
            <strong>Search scope</strong>
            <select
              value={scope}
              onChange={(e) => { setScope(e.target.value); setSelectedEventId(""); setSelectedAlbumId(""); }}
              style={{ display: "block", marginTop: "0.25rem", padding: "0.4rem 0.6rem", borderRadius: 6, border: "1px solid #ccc" }}
            >
              <option value="gallery">My Gallery (all photos)</option>
              <option value="event">Specific Event</option>
              <option value="album">Specific Album</option>
            </select>
          </label>

          {(scope === "event" || scope === "album") && (
            <label style={{ marginTop: "0.75rem", display: "block" }}>
              Select Event
              <select
                value={selectedEventId}
                onChange={(e) => { setSelectedEventId(e.target.value); setSelectedAlbumId(""); }}
                style={{ display: "block", marginTop: "0.25rem", padding: "0.4rem 0.6rem", borderRadius: 6, border: "1px solid #ccc" }}
              >
                <option value="">{eventsError ? "Error loading events" : events.length === 0 ? "No events available" : "— choose an event —"}</option>
                {events.map((ev) => (
                  <option key={ev.id} value={ev.id}>{ev.name} ({ev.event_date})</option>
                ))}
              </select>
              {eventsError && <small style={{ color: "#e53e3e" }}>{eventsError}</small>}
            </label>
          )}

          {scope === "album" && selectedEventId && (
            <label style={{ marginTop: "0.75rem", display: "block" }}>
              Select Album
              <select
                value={selectedAlbumId}
                onChange={(e) => setSelectedAlbumId(e.target.value)}
                style={{ display: "block", marginTop: "0.25rem", padding: "0.4rem 0.6rem", borderRadius: 6, border: "1px solid #ccc" }}
              >
                <option value="">{albumsError ? "Error loading albums" : albums.length === 0 ? "No albums available" : "— choose an album —"}</option>
                {albums.map((al) => (
                  <option key={al.id} value={al.id}>{al.name}</option>
                ))}
              </select>
              {albumsError && <small style={{ color: "#e53e3e" }}>{albumsError}</small>}
            </label>
          )}
        </div>

        {error && <p className="form-error">{error}</p>}

        <button className="primary-button selfie-submit" onClick={searchPhotos} disabled={searching}>
          {searching ? "Searching…" : "Find My Photos"}
        </button>

        {/* Camera modal */}
        {cameraOpen && (
          <div className="modal" role="dialog" aria-modal="true" aria-label="Take a selfie">
            <div className="camera-modal">
              <button className="close-button" onClick={stopCamera} aria-label="Close camera">×</button>
              <video ref={videoRef} autoPlay playsInline muted />
              <div className="camera-actions">
                <button className="secondary-button" onClick={stopCamera}>Cancel</button>
                <button className="primary-button" onClick={capture}>Capture selfie</button>
              </div>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
