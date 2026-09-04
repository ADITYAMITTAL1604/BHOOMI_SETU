FROM python:3.11-slim

# System deps required by psycopg2, geopandas, shapely, and healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer-cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application source
COPY . .

# Ensure storage directory exists and has permissions
RUN mkdir -p /app/storage/documents /app/ml/models && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
