FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user
RUN groupadd -r geoagriuser && useradd --no-log-init -r -g geoagriuser geoagriuser

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements-prod.txt /app/
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy project files
COPY . /app

# Fix permissions
RUN chown -R geoagriuser:geoagriuser /app

# Collect static files
USER geoagriuser
RUN python manage.py collectstatic --noinput

# Expose port and run
EXPOSE 8080
CMD ["gunicorn", "geoagri.wsgi:application", "--bind", "0.0.0.0:8080"]
