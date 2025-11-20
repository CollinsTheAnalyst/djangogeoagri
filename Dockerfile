# 1. Base Image
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Create non-root user
RUN groupadd -r geoagriuser && useradd --no-log-init -r -g geoagriuser geoagriuser

WORKDIR /app

# System dependencies (requires root)
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/lib/x86_64-linux-gnu/libgdal.so /usr/lib/libgdal.so

COPY requirements-prod.txt /app/
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . /app

# Fix permissions BEFORE collectstatic
RUN chown -R geoagriuser:geoagriuser /app

# Collect static files (runs as root, OK)
RUN python manage.py collectstatic --noinput

# Fix permissions again AFTER collectstatic (CRITICAL)
RUN chown -R geoagriuser:geoagriuser /app

# Switch to non-root user (Choreo Checkov requirement)
USER geoagriuser

EXPOSE 8080
CMD gunicorn geoagri.wsgi:application --bind 0.0.0.0:$PORT
