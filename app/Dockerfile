# Stage 1: Build the Vite frontend
FROM node:20-slim AS build-stage

WORKDIR /frontend
COPY frontend ./

# Create a safe default .env if one is not present.
RUN if [ ! -f .env ]; then \
      printf "VITE_AUTH_URL=\nVITE_AUTH_ENABLED=false\n" > .env; \
    fi

RUN npm ci
RUN npm run build

# Stage 2: Python runtime with slim base
FROM python:3.11-slim AS production-stage

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python dependencies first (layer caching)
COPY ./backend/requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY ./backend/ /app

# Provide menu metadata to the backend at runtime (used for extras/category rules).
RUN mkdir -p /app/data
COPY ./frontend/src/data/menuItems.json /app/data/menuItems.json

# Pre-build ChromaDB data from menu items (local vector search)
COPY ./ingest_menu_local.py /tmp/ingest_menu_local.py
ENV CHROMA_DATA_PATH=/app/chroma_data
ENV CHROMA_COLLECTION_NAME=menu_items
ENV MENU_ITEMS_PATH=/app/data/menuItems.json
RUN python /tmp/ingest_menu_local.py && rm /tmp/ingest_menu_local.py

# Copy the freshly-built frontend assets
COPY --from=build-stage /backend/static /app/static

CMD ["python3", "-m", "gunicorn", "app:create_app", "-b", "0.0.0.0:8000", "--worker-class", "aiohttp.GunicornWebWorker"]
