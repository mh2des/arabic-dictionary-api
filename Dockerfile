# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build database if dict.db doesn't exist
RUN if [ ! -f dict.db ]; then \
        echo "Building database..." && \
        python scripts/build_db.py --skip-download || echo "DB build failed, will use empty DB"; \
    fi

EXPOSE 8080

ENV SQLITE_DB=/app/dict.db
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
