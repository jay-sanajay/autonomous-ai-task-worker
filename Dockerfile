# ==============================================================================
# AgentOS Autonomous AI Task Worker - Multi-Stage Production Dockerfile
# Optimized for Render, Fly.io, Cloud Run, and container deployments
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build React Frontend
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Python Backend & Web Service
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=10000

WORKDIR /app

# Install minimal system tools (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application, templates, datasets, and serverless helpers
COPY backend/ ./backend/
COPY sandbox_data/ ./sandbox_data/
COPY api/ ./api/

# Copy compiled frontend from Stage 1 so FastAPI serves UI directly
COPY --from=frontend-builder /app/dist ./dist
COPY --from=frontend-builder /app/dist ./frontend/dist

# Expose Render web port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-10000}/api/health || exit 1

# Start Uvicorn bound to dynamic Render $PORT
CMD ["sh", "-c", "exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
