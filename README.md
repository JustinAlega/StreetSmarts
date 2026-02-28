# PickHacksSP26

Real-time urban safety intelligence platform for St. Louis. Combines crime data, community reports, and AI analysis into an interactive safety map.

## Features

- **Safety Heatmap** — Color-coded risk overlay on a Mapbox map
- **Safety-Optimized Routing** — A* pathfinding balancing shortest vs. safest path
- **Community Live Feed** — Users post real-time safety reports, AI classifies severity & category
- **Location Risk Summary** — Click anywhere for a risk breakdown with recommendations

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite + TypeScript |
| Map | Mapbox GL JS |
| Backend | FastAPI (Python 3.11+) |
| Database | SQLite |
| Routing | OSMnx + NetworkX |
| AI | Google Gemini (gemini-2.0-flash) |
| Hosting | Vultr VPS (Docker) |

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- API keys: [Mapbox](https://mapbox.com) + [Google Gemini](https://aistudio.google.com)

### 1. Clone & configure

```bash
git clone https://github.com/<your-org>/PickHacksSP26.git
cd PickHacksSP26
cp .env.example .env
# Edit .env and fill in MAPBOX_TOKEN and GEMINI_API_KEY
```

### 2. Run the backend (Docker)

```bash
docker compose up --build
```

Backend is live at **http://localhost:8000**
Swagger docs at **http://localhost:8000/docs**

### 3. Run the backend (without Docker)

```bash
cd backend
python -m venv venv
venv\Scripts\activate         # Windows
# source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend is live at **http://localhost:5173**

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/heatmap-data` | GeoJSON risk points for map |
| POST | `/api/route` | Safety-optimized walking route |
| POST | `/api/post` | Submit a community safety report |
| GET | `/api/feed` | Get nearby community posts |
| GET | `/api/location-summary` | Risk breakdown for a location |

## Deploying to Vultr

```bash
ssh root@<your-vultr-ip>
curl -fsSL https://get.docker.com | sh
git clone https://github.com/<your-org>/PickHacksSP26.git
cd PickHacksSP26
cp .env.example .env && nano .env
docker compose up -d --build
# Verify: curl http://localhost:8000/health
```

## Environment Variables

| Variable | Description | Get it at |
|----------|-------------|-----------|
| `MAPBOX_TOKEN` | Mapbox map tiles | https://mapbox.com |
| `GEMINI_API_KEY` | Google Gemini AI | https://aistudio.google.com |