import React, { useRef, useState } from "react";
import API from "../services/api";
import { authHeaders, authToken, saveSession, session } from "../services/auth";
import WatermarkPanel from "../components/WatermarkPanel";

export default function Profile() {
  const user = session();
  const [fullName, setName] = useState(user?.full_name || "");
  const [avatarUrl, setAvatar] = useState(user?.avatar_url || "");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const fileRef = useRef();
  if (!user) return <main className="empty-state"><h1>Please sign in</h1><p>Your profile is available once you are signed in.</p></main>;

  const persistUser = (data) => saveSession({ token: authToken(), user: data });
  const uploadAvatar = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const data = new FormData(); data.append("file", file);
    setUploadingAvatar(true); setMessage("");
    try { const response = await API.post("/auth/me/avatar", data, { headers: authHeaders() }); setAvatar(response.data.avatar_url); persistUser(response.data); setMessage("Profile photo updated."); }
    catch (err) { setMessage(err.response?.data?.detail || "Could not upload your profile photo."); }
    finally { setUploadingAvatar(false); event.target.value = ""; }
  };
  const save = async (event) => {
    event.preventDefault(); setSaving(true); setMessage("");
    try { const { data } = await API.put("/auth/me", { full_name: fullName, avatar_url: avatarUrl }, { headers: authHeaders() }); persistUser(data); setMessage("Profile updated successfully."); }
    catch (err) { setMessage(err.response?.data?.detail || "Could not update your profile."); }
    finally { setSaving(false); }
  };
  return <main className="content-shell"><section className="profile-card">
    <div className="avatar-editor"><div className="profile-avatar">{avatarUrl ? <img src={avatarUrl} alt="Profile" /> : fullName.charAt(0).toUpperCase()}</div><button type="button" className="avatar-edit-button" onClick={() => fileRef.current?.click()} disabled={uploadingAvatar}>{uploadingAvatar ? "Uploading..." : "Change photo"}</button><input ref={fileRef} className="visually-hidden" type="file" accept="image/jpeg,image/png,image/webp" onChange={uploadAvatar} /></div>
    <div><p className="eyebrow">ACCOUNT SETTINGS</p><h1>My profile</h1><p className="muted">Add a recognizable photo and keep your details current.</p></div>
    <form onSubmit={save}><label>Full name<input value={fullName} onChange={(e) => setName(e.target.value)} required minLength="2" /></label><label>Profile photo URL <span className="optional">Optional</span><input type="url" value={avatarUrl} onChange={(e) => setAvatar(e.target.value)} placeholder="https://example.com/photo.jpg" /></label><button className="primary-button" disabled={saving}>{saving ? "Saving..." : "Save changes"}</button>{message && <p className="success-message">{message}</p>}</form>
  <WatermarkPanel /></section></main>;
}
