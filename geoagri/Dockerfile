# 1. Base Image
FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
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

# Copy requirements and install
COPY requirements-prod.txt /app/
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy app code
COPY . /app

# Create non-root user with explicit UID/GID
RUN groupadd -g 10014 geoagriuser \
    && useradd -u 10014 -g geoagriuser -m geoagriuser \
    && chown -R 10014:10014 /app

# Collect static files as root
RUN python manage.py collectstatic --noinput

# Fix permissions again
RUN chown -R 10014:10014 /app

# Switch to non-root user
USER 10014

EXPOSE 8080
CMD ["sh", "-c", "gunicorn geoagri.wsgi:application --bind 0.0.0.0:${PORT:-8080}"]