import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";

import API from "./services/api";
import { saveSession } from "./services/auth";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

import Home from "./pages/Home";
import UploadPhotos from "./pages/UploadPhotos";
import UploadSelfie from "./pages/UploadSelfie";
import Results from "./pages/Results";
import Auth from "./pages/Auth";
import Profile from "./pages/Profile";
import MyGallery from "./pages/MyGallery";
import Events from "./pages/Events";
import EventDetail from "./pages/EventDetail";
import AlbumDetail from "./pages/AlbumDetail";
import People from "./pages/People";
import PersonDetail from "./pages/PersonDetail";

function HashTokenListener() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const raw = window.location.hash.slice(1) || window.location.search.slice(1);
    const params = new URLSearchParams(raw);
    const token = params.get("token");
    if (!token) return;

    API.get("/auth/me", { headers: { Authorization: `Bearer ${token}` } })
      .then(({ data }) => {
        saveSession({ token, user: data });
        window.history.replaceState(null, "", location.pathname + location.search);
        navigate("/");
      })
      .catch(() => {
        window.history.replaceState(null, "", location.pathname + location.search);
      });
  }, [location.key, location.pathname, location.search, navigate]);

  return null;
}

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <HashTokenListener />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/upload-event" element={<ProtectedRoute element={<UploadPhotos />} />} />
        <Route path="/upload-selfie" element={<ProtectedRoute element={<UploadSelfie />} />} />
        <Route path="/results" element={<ProtectedRoute element={<Results />} />} />
        <Route path="/signin" element={<Auth />} />
        <Route path="/profile" element={<ProtectedRoute element={<Profile />} />} />
        <Route path="/my-gallery" element={<ProtectedRoute element={<MyGallery />} />} />
        <Route path="/events" element={<ProtectedRoute element={<Events />} />} />
        <Route path="/events/:eventId" element={<ProtectedRoute element={<EventDetail />} />} />
        <Route path="/events/:eventId/albums/:albumId" element={<ProtectedRoute element={<AlbumDetail />} />} />
        <Route path="/people" element={<ProtectedRoute element={<People />} />} />
        <Route path="/people/:clusterId" element={<ProtectedRoute element={<PersonDetail />} />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
