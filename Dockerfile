FROM python:3.11-slim-bookworm

# Prevent Python from creating .pyc files
# and make stdout/stderr appear immediately in Render logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Native runtime/build dependencies.
# sqlite3 is required by Mem0's SQLiteManager.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for Docker layer caching.
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy application.
COPY app ./app

# Render provides PORT at runtime.
ENV PORT=10000

EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]