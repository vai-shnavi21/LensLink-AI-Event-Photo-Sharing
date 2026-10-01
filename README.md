LensLink – AI-Powered Event Photo Sharing Platform

LensLink is an AI-powered event photo-sharing platform that allows photographers to create events and albums, upload event photos, and help guests quickly find their personal photos using AI-based face recognition.

The platform is designed for weddings, college events, parties, conferences, and other large gatherings where users need an easy way to find and download their photos without manually searching through hundreds or thousands of images.

Features

📸 Event & Album Management

Create and manage events

Add multiple albums to an event

Organize photos into albums

Add and remove photos from albums

View event-specific photo galleries

Map photos to specific albums

🤖 AI Face Recognition

Upload one or multiple selfies

Detect faces in uploaded selfies

Generate face embeddings using InsightFace

Search event photos using selected selfies

Identify photos containing matching people

Search photos of multiple people using multiple selfies

Supports cloud-hosted event photos

AI-powered "Find My Photos" workflow

☁️ Cloud Image Storage

Event photos stored using Cloudinary

Selfies stored securely in Cloudinary

Cloud URLs used instead of local image storage

CDN-based image delivery

Reduces backend disk-space requirements

Supports processing of cloud-hosted event photos

🔗 Event Link Sharing

Generate a unique shareable link for an event

Share events through WhatsApp, email, SMS, and messaging apps

Guests can open the event directly in a browser

No mobile application required for guests

Guests do not need to create an account just to access a shared event

Guests can browse all event albums

Guests can use AI-powered "Find My Photos"

Guests can upload selfies

Guests can download their photographs

Works on mobile, tablet, laptop, and desktop browsers

📱 QR Code Event Sharing

Generate a unique QR code for an event

Generate branded high-resolution QR codes

Download QR code as a high-resolution PNG

Print QR codes on table cards, invitations, standees, banners, and photo booth walls

Guests scan the QR code and directly open the event gallery

QR code provides quick access to the AI photo search workflow

📤 Guest Photo Uploads

Guests can upload their own event photographs

Uploaded guest photos can be added to the event gallery

Supports JPEG, JPG, PNG, WebP, and GIF images

Cloudinary can be used for guest photo storage

📥 High-Resolution Downloads

Guests can download event photographs in high resolution

Designed to preserve available image quality

Useful for printing, sharing, and personal archiving

💧 Watermark Management

Automatically apply watermarks to uploaded photographs

Protect photographer branding and copyrighted work

Add custom watermark text

Add photographer logo

Add sponsor logo

Support photographer + sponsor dual-logo branding

Configure watermark opacity/transparency

Configure watermark position

Apply watermark to multiple photographs

🖼️ Custom Watermark Image

Upload a custom high-resolution PNG watermark/logo

Use custom photography business logos

Use custom text such as:
© 2026 Vaishnavi Photography

Support custom branding for individual events

🎨 Watermark Position & Transparency

Watermark position can be configured, for example:

Top-left

Top-right

Bottom-left

Bottom-right

Center

Diagonal

Tiled/repeated

Watermark transparency/opacity can also be configured.

👤 Album-Specific Watermark Settings

Enable or disable watermarking for specific albums

Configure different watermark behavior for different albums

Example:

Rahul & Priya Wedding

Ceremony
    Watermark: ON

Reception
    Watermark: ON

Candid Moments
    Watermark: OFF

🏷️ Dual Logo / Sponsor Watermark

Support branding with:

Photographer logo

Sponsor logo

Photographer + sponsor logo combination

This can be useful for sponsored events, college festivals, corporate events, and photography partnerships.

👀 Preview & Download Watermarks

LensLink can use different watermark settings for preview images and downloaded images.

Example:

Photo Upload
     ↓
Preview Watermark
     ↓
Guest Views Photo
     ↓
Purchase / Approval / Authorized Download
     ↓
Configured Download Version

🛒 Photo Sale / Purchase Watermark Workflow

For events where photographs are sold, a possible workflow is:

Photographer Uploads Photo
          ↓
Preview Watermark Applied
          ↓
Guest Views Watermarked Photo
          ↓
Purchase / Photographer Approval
          ↓
Watermark Removed
          ↓
Clean High-Resolution Photo Delivered

The exact watermark-removal condition depends on the application's configured payment, password, or photographer-approval workflow.

🔐 Authentication & Security

Email/password authentication

Google OAuth authentication

JWT/Bearer-token based authorization

Password hashing

Protected upload endpoints

User-specific photo access

Google OAuth accounts cannot be accessed using password authentication

🖼️ Gallery

Personal photo gallery

Event photo browsing

Album-based browsing

Cloudinary image URLs

Photo deletion support

High-quality image access

AI-matched photo results

High-resolution downloads

📱 User-Friendly Interface

Responsive React interface

Mobile-friendly design

Desktop and tablet support

Event and album navigation

Selfie upload interface

Multiple-selfie selection

AI-powered "Find My Photos" workflow

Event sharing interface

QR code generation

Watermark configuration

Project Overview

LensLink solves a common problem at events.

For example, consider a wedding:

Event: Rahul & Priya Wedding

The photographer can create:

Rahul & Priya Wedding
│
├── Ceremony
├── Reception
├── Candid Moments
├── Family Photos
└── Couple Photos

The photographer uploads hundreds or thousands of photographs and then generates an event link or QR code for guests.

A guest can:

Open the event.

Browse event albums.

Upload one or multiple selfies.

LensLink detects the face.

The system generates face embeddings.

The embeddings are compared with faces detected in event photographs.

Matching photographs are returned.

The guest can view the photographs.

The guest can download high-resolution photographs.

The guest can also upload their own event photographs.

This eliminates the need to manually search through hundreds or thousands of event photographs.



Event Link Sharing Flow

Photographer
     ↓
Create Event
     ↓
Upload Photos
     ↓
Create Albums
     ↓
Generate Event Link
     ↓
Share Link
     ↓
Guest Opens Link
     ↓
Event Gallery
     ↓
Browse Albums / Find My Photos
     ↓
Upload Selfie
     ↓
AI Face Recognition
     ↓
Matching Photos
     ↓
View / Download

Guests can open the shared event in a browser without installing a mobile application.


QR Code Sharing Flow

Create Event
     ↓
Generate QR Code
     ↓
Download High-Resolution QR
     ↓
Print / Display QR
     ↓
Guest Scans QR
     ↓
Event Gallery Opens
     ↓
Browse Albums
     ↓
Find My Photos



Guest Photo Upload Flow

Guest Opens Event
       ↓
Select Guest Upload
       ↓
Select Photograph(s)
       ↓
Upload
       ↓
Cloudinary Storage
       ↓
Event Gallery

Watermark Flow

Photographer Uploads Photo
          ↓
Check Watermark Settings
          ↓
Watermark Enabled?
     ┌────┴────┐
    YES         NO
     │           │
     ▼           ▼
Apply Logo/Text  Original Flow
     │
     ▼
Preview Image
     │
     ▼
Guest Views Photo
     │
     ▼
Download  / Approval
     │
     ▼
Configured Download Version



Technical Architecture

Frontend

React

JavaScript

HTML

CSS

React Router

Backend

Python

FastAPI

REST APIs

AI / Computer Vision

InsightFace

ONNX Runtime

OpenCV

NumPy

Face Embeddings

Face Similarity Matching



Database

PostgreSQL / SQLite depending on deployment configuration

Cloud Storage

Cloudinary

Authentication

JWT

Google OAuth

Password hashing

Deployment

Frontend: Vercel

Backend: Render / compatible Python hosting

Image storage: Cloudinary

Database: PostgreSQL-compatible cloud database where configured



System Architecture

                    ┌──────────────────────┐
                    │       User           │
                    │ Photographer / Guest │
                    └──────────┬───────────┘
                               │
                     Event Link / QR Code
                               │
                               ▼
                    ┌──────────────────────┐
                    │   React Frontend     │
                    │      LensLink        │
                    └──────────┬───────────┘
                               │
                         REST API / JWT
                               │
                               ▼
                    ┌──────────────────────┐
                    │   FastAPI Backend    │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
       ┌───────────┐    ┌────────────┐    ┌─────────────┐
       │ PostgreSQL│    │ Cloudinary │    │ InsightFace │
       │ / SQLite  │    │   Storage  │    │  AI Model   │
       └───────────┘    └────────────┘    └──────┬──────┘
                                                 │
                                                 ▼
                                          Face Embeddings
                                                 │
                                                 ▼
                                          Photo Matching

AI Photo Search Architecture

                   Event Photos
                        │
                        ▼
                Cloudinary Storage
                        │
                        ▼
                Download Image Data
                        │
                        ▼
                  OpenCV Processing
                        │
                        ▼
                  Face Detection
                        │
                        ▼
                Face Embeddings
                        │
                        │
                        │ Compare
                        │
                        ▼
                   Selfie Upload
                        │
                        ▼
                  Face Detection
                        │
                        ▼
                Selfie Embedding
                        │
                        ▼
                Similarity Matching
                        │
                        ▼
               Matching Event Photos



API Endpoints

Authentication

POST /auth/login
POST /auth/register
GET  /auth/google/login
GET  /auth/google/callback

Events

GET    /events
POST   /events
GET    /events/{event_id}
PUT    /events/{event_id}
DELETE /events/{event_id}

Albums

GET    /events/{event_id}/albums
POST   /events/{event_id}/albums
PUT    /albums/{album_id}
DELETE /albums/{album_id}

Album Photos

GET    /albums/{album_id}/photos
POST   /albums/{album_id}/photos
DELETE /albums/{album_id}/photos/{photo_id}

Gallery

POST   /gallery/upload
GET    /gallery
GET    /gallery/{photo_id}
DELETE /gallery/{photo_id}

Cloud Upload

Event Photos

POST /upload/event-photos

Selfie

POST /upload/selfie

Environment Variables

Create a .env file inside the backend directory.

Example:

APP_SECRET=your_secret_key

DATABASE_URL=your_database_url

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

FRONTEND_ORIGINS=http://localhost:3000

PYTHON_VERSION=3.10



Use .env.example with placeholder values instead.

Local Installation

1. Clone Repository

git clone <repository-url>
cd LensLink

2. Backend Setup

cd backend

Create a virtual environment:

python -m venv venv

Windows:

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Configure the .env file.

Start the FastAPI server:

uvicorn app:app --reload

Backend:

http://localhost:8000



3. Frontend Setup

Open another terminal:

cd frontend/frontend

Install dependencies:

npm install

Start the React application:

npm start

Frontend:

http://localhost:3000



⚠️ Known Deployment Limitation – Backend Memory / Subscription

LensLink uses AI-based face recognition and image-processing libraries that can require significant memory.

The backend uses:

InsightFace

ONNX Runtime

OpenCV

NumPy

These components can consume substantial RAM when the AI model is loaded and when event images are processed.

During deployment testing, the backend hosting service can exceed the available memory limit while performing photo retrieval and AI face processing.

Typical Problem

Backend Deployment
       ↓
FastAPI Starts
       ↓
InsightFace / ONNX Model Loads
       ↓
AI Image Processing
       ↓
Memory Usage Increases
       ↓
Available Hosting Memory Exceeded
       ↓
Backend Restart / Service Failure

Observed Impact

When the backend reaches its memory limit:

Backend service may restart.

API requests may fail.

AI face recognition may become unavailable.

Photo retrieval may fail.

Event/album API requests may become unavailable.

The frontend may display network or API errors.

Subscription / Additional Resource Requirement

The issue is related to the backend hosting resource limit.

A free or limited-memory hosting environment may not provide enough RAM for the AI face-recognition workload.

Therefore, reliable deployment may require a hosting plan or backend environment with additional memory resources.

This does not mean that the React frontend or Cloudinary storage itself requires the same additional resources.

The main resource requirement is for the backend because it loads and executes the AI model and performs image processing.


During deployment, the available memory of the selected hosting environment becomes an additional constraint.

Local Environment
      ↓
Sufficient RAM
      ↓
AI Model + Photo Processing
      ↓
Photo Retrieval Works


Limited Hosting Environment
      ↓
Restricted RAM
      ↓
AI Model + Photo Processing
      ↓
Memory Limit
      ↓
Backend May Restart / Fail

