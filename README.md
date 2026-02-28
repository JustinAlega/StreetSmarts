# 🛡️ StreetSmarts

**Real-time safety intelligence for Saint Louis, MO.**

StreetSmarts is a full-stack web application that provides pedestrians with live safety insights, risk heatmaps, optimized walking routes, and community-sourced incident reports — all powered by AI and real-world data.

![Tech Stack](https://img.shields.io/badge/React-19-blue?logo=react)
![Tech Stack](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![Tech Stack](https://img.shields.io/badge/Gemini_AI-2.0_Flash-orange?logo=google)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🗺️ **Interactive Safety Map** | Mapbox GL-powered map centered on Saint Louis with click-to-inspect locations |
| 🔥 **Risk Heatmap Overlay** | Gaussian-splatted raster tile layer showing per-location risk intensity |
| 🚶 **Safety-Optimized Routing** | Walking directions via Mapbox Directions API with risk scoring and route alternatives |
| 📊 **Location Summaries** | Per-coordinate safety reports with category breakdowns (crime, transport, weather, etc.) |
| 💬 **Community Feed** | Submit and browse safety reports; posts are classified by Gemini AI for severity and category |
| 🏠 **Nearby Safe Locations** | Discover nearby low-risk points of interest |
| 🤖 **AI-Powered Pipeline** | Multi-agent system (observer → scraper → criticality → validator) for ingesting live safety data |

---

## 🏗️ Architecture

```
StreetSmarts/
├── backend/                  # FastAPI server (Python 3.11)
│   ├── main.py               # App entry point & CORS config
│   ├── routes/
│   │   ├── heatmap.py        # Raster tile server for risk heatmap
│   │   ├── routing.py        # Safety-optimized walking routes
│   │   ├── social.py         # Community post feed + Gemini classification
│   │   └── location_summary.py  # Per-location risk reports
│   ├── live_pipeline/        # Multi-agent AI data ingestion
│   │   ├── pipeline.py       # Orchestrator
│   │   ├── observer_agent.py # Monitors for new data sources
│   │   ├── scraper_agent.py  # Web scraping via Browserbase
│   │   ├── criticality_agent.py  # Scores incident severity
│   │   ├── validator_agent.py    # Cross-validates data
│   │   ├── query_planner.py  # Plans search queries
│   │   └── locations.py      # STL location definitions
│   ├── db/
│   │   ├── database.py       # SQLite schema & init
│   │   └── db_writer.py      # CRUD operations
│   ├── data_gen.py           # Seed data generator
│   ├── run_seed.py           # Run seeding script
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # React + Vite (Node 20)
│   ├── src/
│   │   ├── App.jsx           # Router & main layout
│   │   ├── components/
│   │   │   ├── MapView.jsx       # Mapbox GL map with heatmap & routes
│   │   │   ├── RoutePanel.jsx    # Route input & display panel
│   │   │   ├── SummaryPanel.jsx  # Location safety summary popup
│   │   │   ├── MapHeader.jsx     # Top toolbar with toggle controls
│   │   │   └── MapLegend.jsx     # Heatmap color legend
│   │   ├── pages/
│   │   │   └── LocationFeedPage.jsx  # Community feed page
│   │   ├── lib/              # Utility functions
│   │   └── index.css         # Global styles
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── nginx.conf            # Production Nginx config
│   └── Dockerfile
├── docker-compose.yml        # Full-stack orchestration
└── .env                      # Root-level env vars for Docker Compose
```

---

## 🚀 Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v20+ with Docker Compose v2)
- API keys (see [Environment Variables](#-environment-variables))

### 1. Clone the Repository

```bash
git clone https://github.com/JustinAlega/StreetSmarts.git
cd StreetSmarts
```

### 2. Set Up Environment Variables

The project requires environment files at three levels. Example files are provided — copy and fill them in:

**Root `.env`** (used by Docker Compose):

```bash
cp .env.example .env   # if .env.example exists, otherwise create manually
```

```env
# .env (root)
VITE_API_URL=http://localhost:8000
VITE_MAPBOX_TOKEN=your-mapbox-token-here
```

**Backend `backend/.env`**:

```bash
cp backend/.env.example backend/.env
```

```env
# backend/.env
GEMINI_API_KEY=your-gemini-api-key
MAPBOX_TOKEN=your-mapbox-token
BROWSERBASE_API_KEY=your-browserbase-key
BROWSERBASE_PROJECT_ID=your-browserbase-project-id
FBI_API_KEY=your-fbi-api-key
DB_PATH=/app/data/app.db
```

**Frontend `frontend/.env`**:

```bash
cp frontend/.env.example frontend/.env
```

```env
# frontend/.env
VITE_MAPBOX_TOKEN=your-mapbox-token-here
```

### 3. Run with Docker Compose (Recommended)

```bash
docker compose up --build
```

This will:
1. **Build the backend** — installs Python dependencies, GIS libraries, copies the seed database
2. **Build the frontend** — installs npm packages, builds the React app with Vite, serves via Nginx
3. **Start both services** — backend health check runs before the frontend starts

Once you see output like:

```
backend-1   | [SERVER] StreetSmarts backend ready for Saint Louis, MO
frontend-1  | Configuration complete; ready for start up
```

The app is live:

| Service | URL |
|---------|-----|
| **Frontend** | [http://localhost](http://localhost) (port 80) |
| **Backend API** | [http://localhost:8000](http://localhost:8000) |
| **API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **Health Check** | [http://localhost:8000/health](http://localhost:8000/health) |

To stop:

```bash
docker compose down
```

---

## 🖥️ Local Development (Without Docker)

If you prefer to run the services directly for faster iteration:

### Backend

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Set DB_PATH for local development
# In backend/.env, change:
#   DB_PATH=/app/data/app.db  →  DB_PATH=./app.db

# Start the server with hot reload
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend dev server will be available at `http://localhost:5173`.

> **Note:** In local dev mode, the frontend Vite dev server proxies API requests. Make sure `VITE_API_URL` in `frontend/.env` (or the root `.env`) points to `http://localhost:8000` if it isn't set by default.

---

## 🔑 Environment Variables

| Variable | Location | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | `backend/.env` | Google Gemini API key for AI classification and pipeline agents |
| `MAPBOX_TOKEN` | `backend/.env` | Mapbox access token (used by backend for Directions API) |
| `VITE_MAPBOX_TOKEN` | `frontend/.env`, root `.env` | Mapbox access token (used by frontend map rendering) |
| `VITE_API_URL` | root `.env` | Backend API URL (default: `http://localhost:8000`) |
| `BROWSERBASE_API_KEY` | `backend/.env` | Browserbase API key for headless scraping in the live pipeline |
| `BROWSERBASE_PROJECT_ID` | `backend/.env` | Browserbase project identifier |
| `FBI_API_KEY` | `backend/.env` | FBI Crime Data API key for crime statistics |
| `DB_PATH` | `backend/.env` | SQLite database file path (`/app/data/app.db` for Docker, `./app.db` for local) |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service info and status |
| `GET` | `/health` | Health check with database row count |
| `GET` | `/tiles/{z}/{x}/{y}.png` | Heatmap raster tile (slippy map format) |
| `POST` | `/route` | Compute a safety-optimized walking route |
| `GET` | `/location-summary?lat=...&lng=...` | Get safety summary for a coordinate |
| `POST` | `/post` | Submit a community safety report |
| `GET` | `/feed?lat=...&lng=...&radius_km=...` | Get nearby community reports |

### Route Request Body

```json
{
  "start_lat": 38.6270,
  "start_lng": -90.1994,
  "end_lat": 38.6350,
  "end_lng": -90.2045,
  "priority": "safety"
}
```

---

## 🧠 AI Pipeline

StreetSmarts uses a multi-agent pipeline to continuously enrich its safety database:

```
┌─────────────┐    ┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Observer    │ →  │  Query      │ →  │  Scraper         │ →  │  Criticality    │
│  Agent       │    │  Planner    │    │  Agent           │    │  Agent          │
│              │    │             │    │  (Browserbase)   │    │  (Gemini)       │
└─────────────┘    └─────────────┘    └──────────────────┘    └────────┬────────┘
                                                                       │
                                                              ┌────────▼────────┐
                                                              │  Validator      │
                                                              │  Agent          │
                                                              │  (Gemini)       │
                                                              └────────┬────────┘
                                                                       │
                                                              ┌────────▼────────┐
                                                              │  SQLite DB      │
                                                              │  (truth table)  │
                                                              └─────────────────┘
```

Each agent uses **Google Gemini 2.0 Flash** for natural language understanding, classification, and validation.

---

## 🗄️ Database Schema

SQLite with two core tables:

**`posts`** — Community-submitted safety reports:
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-incrementing primary key |
| `lat`, `lng` | REAL | Report coordinates |
| `content` | TEXT | Report text |
| `severity` | REAL | AI-classified severity (0.0–1.0) |
| `category` | TEXT | Incident category |
| `human` | INTEGER | 1 = user-submitted, 0 = AI-generated |
| `created_at` | TIMESTAMP | Creation time |

**`truth`** — Per-location risk vectors:
| Column | Type | Description |
|--------|------|-------------|
| `lat`, `lng` | REAL | Location (composite primary key) |
| `crime` | REAL | Crime risk score |
| `public_safety` | REAL | Public safety risk |
| `transport` | REAL | Transportation risk |
| `infrastructure` | REAL | Infrastructure risk |
| `policy` | REAL | Policy-related risk |
| `protest` | REAL | Protest/civil unrest risk |
| `weather` | REAL | Weather-related risk |
| `other` | REAL | Uncategorized risk |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite 7, Mapbox GL JS, React Router |
| **Backend** | FastAPI, Uvicorn, Python 3.11 |
| **AI** | Google Gemini 2.0 Flash |
| **Database** | SQLite (via aiosqlite) |
| **Scraping** | Browserbase (headless browser) |
| **Maps** | Mapbox GL + Mapbox Directions API |
| **Deployment** | Docker Compose, Nginx |
| **Data** | FBI Crime Data API, OSMnx (street graph) |

---

## 📄 License

This project was built for [PickHacks 2026](https://pickhacks.io/).
