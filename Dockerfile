# ----------------------------------------------------
# 🚨 CACHE BUSTING LINE (CHANGE VALUE TO TODAY'S DATE OR A RANDOM NUMBER) 🚨
# This line forces the build system to re-read the file and apply the security fix.
ARG BUILD_DATE=20251121d 
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
# 🚀 SECURITY FIX: Create User (Compliant UID 10001)
# -----------------------------------------------
# Create user with explicit UID and GID 10001 (REQUIRED by CKV_CHOREO_1)
RUN groupadd -r geoagriuser -g 10001 && useradd -r -u 10001 -g geoagriuser geoagriuser

# Ensure the application user owns the files/folders it will write to
# We use the numerical ID here
RUN chown -R 10001:10001 /app

# Collect Static Files (Gathers assets for Whitenoise serving)
# This runs as root, but permissions are fixed above
RUN python manage.py collectstatic --noinput

# -----------------------------------------------
# 🚀 FINAL SECURITY STEP: Switch User
# -----------------------------------------------
# Switch to the numerical UID 10001 *before* running the application
USER 10001
# -----------------------------------------------

# 5. Define Startup Command
EXPOSE 8080
CMD gunicorn geoagri.wsgi:application --bind 0.0.0.0:$PORT