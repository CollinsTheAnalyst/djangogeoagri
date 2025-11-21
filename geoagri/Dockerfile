# ----------------------------------------------------
# 🚨 CACHE BUSTING LINE (CHANGE VALUE ON FAILURE) 🚨
# This line is necessary to force Choreo's build cache to refresh.
ARG BUILD_DATE=20251121c
# ----------------------------------------------------

# 1. Base Image
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# -----------------------------------------------
# 2. Install Geospatial System Dependencies (Runs as root)
# -----------------------------------------------
# This installs GDAL, GEOS, PROJ, and build essentials required for GeoDjango.
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# CRITICAL: Apply Symlink Fix for GDAL linking
RUN ln -s /usr/lib/x86_64-linux-gnu/libgdal.so /usr/lib/libgdal.so

# -----------------------------------------------
# 3. Setup Application Directory & Install Python
# -----------------------------------------------

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements-prod.txt /app/
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy project code
COPY . /app

# -----------------------------------------------
# 🚀 SECURITY FIX: Create User & Switch (Fixes CKV_DOCKER_3)
# -----------------------------------------------
# 1. Create a non-root user
RUN groupadd -r geoagriuser && useradd --no-log-init -r -g geoagriuser geoagriuser

# 2. Ensure non-root user owns the files (CRITICAL for static files and writing to /app)
RUN chown -R geoagriuser:geoagriuser /app

# 3. Collect Static Files (Gathers assets for Whitenoise serving)
# Runs successfully now that ownership is granted above
RUN python manage.py collectstatic --noinput

# 4. Switch to non-root user *before* running the application
USER geoagriuser
# -----------------------------------------------

# 5. Define Startup Command
EXPOSE 8080
CMD gunicorn geoagri.wsgi:application --bind 0.0.0.0:$PORT