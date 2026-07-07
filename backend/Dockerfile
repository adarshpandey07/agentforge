# syntax=docker/dockerfile:1
# ---------- deps stage: build wheels so the runtime layer stays slim & cached ----------
FROM python:3.11-slim AS deps

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /wheels

# Build tools only needed here, never shipped in the final image
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# ---------- runtime stage ----------
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Install prebuilt wheels (fast, no compiler in the runtime image)
COPY --from=deps /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Non-root user
RUN groupadd -r agentforge && useradd -r -g agentforge -d /app agentforge

COPY --chown=agentforge:agentforge . .

USER agentforge

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
