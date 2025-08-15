FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files including our deployment system
COPY . /app/

# Make sure the new deployment system is executable
RUN chmod +x /app/deploy_real_database.py

# Create app directory structure
RUN mkdir -p /app/app

# Expose port
ENV PORT=8000
EXPOSE $PORT

# Create startup script that forces real database deployment
RUN chmod +x /app/force_real_db.py

# Use a startup command that ensures real database deployment
CMD python3 /app/force_real_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000