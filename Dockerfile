FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Check if database exists, if not, create a minimal one for testing
RUN if [ ! -f app/arabic_dict.db ]; then \
        echo "Database file not found, creating minimal test database..."; \
        python3 -c "import sqlite3; conn = sqlite3.connect('app/arabic_dict.db'); conn.execute('CREATE TABLE entries (id INTEGER PRIMARY KEY, lemma TEXT, pos TEXT)'); conn.execute('INSERT INTO entries (lemma, pos) VALUES (\"test\", \"noun\")'); conn.commit(); conn.close()"; \
    else \
        echo "Database file found, size:"; \
        ls -lh app/arabic_dict.db; \
    fi

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn

# Expose port (default 8000)
ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]