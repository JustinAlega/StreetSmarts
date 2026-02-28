FROM python:3.11-slim

# 1. Install system dependencies for GIS and C-extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    libproj-dev \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of the application
COPY . .

# 4. Create data directory for persistent DB and copy seed DB if present
RUN mkdir -p /app/data /app/cache \
    && if [ -f /app/app.db ]; then cp /app/app.db /app/data/app.db; fi

# 5. Expose FastAPI's default port
EXPOSE 8000

# 6. Start the server using Uvicorn with 2 workers for production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]