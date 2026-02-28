# PickHacksSP26 — Backend Dockerfile
# Build:  docker compose build
# Run:    docker compose up -d

FROM python:3.11-slim AS base

# ---- System deps for OSMnx / GDAL / spatial libs ----
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ \
        libgdal-dev \
        libspatialindex-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- Python deps (cached layer) ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Application code ----
COPY . .

# ---- Persistent data directory ----
# SQLite DB and OSMnx graph cache live here so they survive restarts
RUN mkdir -p /app/persistent
ENV DB_DIR=/app/persistent

EXPOSE 8000

# ---- Entrypoint ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
