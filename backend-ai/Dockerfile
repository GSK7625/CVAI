# ─────────────────────────────────────────────────────────
# FutureCV — Backend AI Service
# Production Dockerfile for Python 3.11 / FastAPI
# ─────────────────────────────────────────────────────────

FROM python:3.11-slim AS base

WORKDIR /app

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ── Install Runtime Python Dependencies ──────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Security: Create Non-Root User ───────────────────────
RUN adduser --disabled-password --gecos "" appuser

# ── Copy Application Code ────────────────────────────────
COPY app ./app

USER appuser

EXPOSE 8000

# ── Healthcheck using stdlib ─────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
