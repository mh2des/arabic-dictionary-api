FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Debug: List files to see what's actually copied
RUN echo "=== FILES IN CONTAINER ===" && \
    ls -la /app && \
    echo "=== Python files ===" && \
    find /app -name "*.py" | head -10

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn

# Test that our standalone app can be imported
RUN python3 -c "from minimal_standalone import app; print('✅ App imports successfully')"

# Expose port (use Railway's $PORT environment variable)
ENV PORT=8000
EXPOSE $PORT

# Default CMD (Railway will override this with railway.json startCommand)
CMD ["python3", "-c", "import uvicorn; from minimal_standalone import app; uvicorn.run(app, host='0.0.0.0', port=8000)"]