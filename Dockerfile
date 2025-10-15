ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY migrations/ ./migrations/

# Create output directories
RUN mkdir -p /app/output /app/logs

# Set Python path
ENV PYTHONPATH=/app

# Default command (can be overridden in docker-compose.yml)
CMD ["python", "--version"]
