import React from "react";
import { API_BASE_URL } from "../services/api";

function PhotoCard({ photo }) {
    // Support both old keys (photo, similarity) and new keys (image_url, similarity_score)
    const url = photo.image_url || photo.photo || "";
    const score = photo.similarity_score ?? photo.similarity ?? null;

    const src = url.startsWith("http") ? url : `${API_BASE_URL}/uploads/event_photos/${url}`;
    const filename = url.split("/").pop().split("?")[0] || "event-photo";

    const downloadImage = async () => {
        try {
            const response = await fetch(src);
            if (!response.ok) throw new Error(`Failed to download: ${response.statusText}`);
            const blob = await response.blob();
            const objectUrl = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = objectUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(objectUrl);
        } catch (err) {
            console.error(err);
            alert("Unable to download image. Please try again.");
        }
    };

    return (
        <article className="photo-card">
            <div className="photo-preview">
                <img src={src} alt={filename} />
            </div>
            <div className="photo-details">
                <h4>{filename}</h4>
                {score !== null && <p>Similarity: <strong>{score}</strong></p>}
            </div>
            <button className="download-button" onClick={downloadImage}>Download</button>
        </article>
    );
}

export default PhotoCard;
