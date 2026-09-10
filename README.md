# 🌊 FloodResQ (FloodFlash)

> **AI-Powered Flood Monitoring, Emergency SOS Triage & Disaster Response Platform**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900?style=flat&logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 Overview

**FloodResQ** is an end-to-end disaster coordination and emergency triage platform designed to accelerate flood response. During severe flood events, emergency helplines often face overwhelming volumes of calls and distress signals. 

FloodResQ bridges this gap by enabling:
- **Instant Citizen Reporting**: Victims or witnesses report flood emergencies with photos, location, and specific needs.
- **Automated AI Triage**: Fast, automated urgency and credibility scoring powered by Google Gemini (with an integrated offline NLP heuristic fallback).
- **Proximity Resource Dispatch**: Nearest emergency response unit (boats, medical teams, food supply, shelters) matched via geospatial calculations.
- **Real-Time Situation Awareness**: Live interactive Leaflet mapping showing urgency clusters, active rescue operations, and field resources.
- **Volunteer Coordination**: Dynamic volunteer registry and dispatch management.

---

## 🛠️ Architecture & Tech Stack

```
FloodFlash/
├── backend/
│   ├── ai_service.py       # Gemini API integration & NLP heuristic triage engine
│   ├── database.py         # SQLAlchemy engine and SQLite session manager
│   ├── geo_service.py      # Haversine distance calculation & nearest resource matching
│   ├── main.py             # FastAPI application, REST endpoints, and static file mounting
│   ├── models.py           # SQLAlchemy database models & Pydantic schemas
│   ├── seed.py             # Initial database seeder for realistic flood disaster demo
│   ├── tests/              # Unit test suite for API verification
│   └── uploads/            # Storage directory for uploaded incident photos
├── frontend/
│   ├── index.html          # Public dashboard & platform overview
│   ├── live-map.html       # Interactive Leaflet emergency map & heatmap
│   ├── report.html         # Incident reporting portal with geolocation & photo upload
│   ├── status.html         # Real-time incident tracker & operational status
│   ├── volunteer.html      # Volunteer signup & coordination portal
│   ├── contact.html        # Emergency contacts and direct hotline directory
│   ├── style.css           # Custom UI design system & responsive styling
│   └── script.js           # Frontend API interactions & client-side routing
├── run.py                  # Entrypoint script for launching the unified server
├── requirements.txt        # Python package dependencies
└── .env.example            # Environment variables template
```

### Technologies Used
- **Backend**: FastAPI (Python), SQLAlchemy ORM, SQLite
- **AI & NLP**: Google Gemini Vision & Text API with intelligent local rule-based heuristic triage fallback
- **Frontend**: HTML5, CSS3, Vanilla JavaScript, Leaflet.js
- **Testing**: Python `unittest` + FastAPI `TestClient`

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+**
- **Git**

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### 3. Set Up a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your **Google Gemini API Key** if cloud AI triage is desired:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
> *Note: If no key is provided, the platform seamlessly defaults to the built-in heuristic NLP triage engine.*

### 6. Run the Application
```bash
python run.py
```

The system will start locally at **`http://127.0.0.1:8000`**.

---

## 🌐 Web Pages & Endpoints

| Page / Endpoint | URL | Description |
|---|---|---|
| **Home Dashboard** | `http://127.0.0.1:8000/` | Main landing page and operational dashboard |
| **Emergency Live Map** | `http://127.0.0.1:8000/live-map.html` | Interactive flood map with incident markers |
| **Submit Report** | `http://127.0.0.1:8000/report.html` | Citizen SOS and incident submission |
| **Track Status** | `http://127.0.0.1:8000/status.html` | Incident tracking and verification |
| **Volunteer Portal** | `http://127.0.0.1:8000/volunteer.html` | Registration and assignment for relief volunteers |
| **Emergency Contacts** | `http://127.0.0.1:8000/contact.html` | Emergency hotline directory |
| **API Documentation** | `http://127.0.0.1:8000/docs` | Interactive Swagger API docs |

---

## 🧪 Running Tests

FloodResQ includes a comprehensive test suite covering health endpoints, database seeding, SOS triage creation, resource matching, and volunteer endpoints.

Execute tests using:
```bash
python -m unittest backend/tests/test_api.py
```

---

## 🚢 Deployment Guide

### Option A: Railway (Recommended — Full App & Database)
Railway deploys the entire application (FastAPI backend + static frontend) on a single URL with zero configuration.

1. Go to [railway.app](https://railway.app) and create a **New Project**.
2. Select **Deploy from GitHub repo** and choose **`FloodResQ`**.
3. Railway automatically detects `Procfile` / `railway.json` and starts the app with Python.
4. *(Optional Database)*: In your Railway project, click **+ New** -> **Database** -> **Add PostgreSQL**.
   - Railway will automatically link the database and provide `DATABASE_URL`.
   - The application automatically switches from SQLite to PostgreSQL with no code changes!
5. *(Optional AI Key)*: In Railway service **Variables**, add `GEMINI_API_KEY` if cloud AI scoring is desired.
6. Under service **Settings** -> **Networking**, click **Generate Domain** to get your public live URL (e.g. `https://floodresq-production.up.railway.app`).

### Option B: Vercel (Frontend CDN)
If you want to host the frontend separately on Vercel's global edge network:

1. Import your `FloodResQ` repository on [vercel.com](https://vercel.com).
2. Set **Root Directory** to `./` (or `frontend`).
3. Vercel will build and serve your static frontend using `vercel.json`.
4. Point the frontend to your deployed Railway backend URL by adding this meta tag inside your HTML `<head>` or setting `window.FLOODRESQ_API_URL`:
   ```html
   <meta name="api-base" content="https://your-railway-app.up.railway.app">
   ```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

