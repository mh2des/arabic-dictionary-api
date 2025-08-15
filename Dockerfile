FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies (gcc, git-lfs, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Ensure git-lfs is initialized and pull LFS files (for database)
RUN git lfs install && git lfs pull

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn

# Expose port (default 8000)
ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]