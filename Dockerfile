# 1. Base Image
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# -----------------------------------------------
# 🚀 SECURITY FIX: Create Non-Root User (Fixes CKV_DOCKER_3)
# -----------------------------------------------
# 1. Create a non-root user and group for security
RUN groupadd -r geoagriuser && useradd --no-log-init -r -g geoagriuser geoagriuser

# Set the working directory inside the container
WORKDIR /app

# 2. Install Geospatial System Dependencies
# This section installs GDAL/GEOS required for GeoDjango
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. Apply Symlink Fix (CRITICAL for GDAL)
RUN ln -s /usr/lib/x86_64-linux-gnu/libgdal.so /usr/lib/libgdal.so

# 4. Copy and Install Python Dependencies
# We use the production requirements file
COPY requirements-prod.txt /app/
RUN pip install --no-cache-dir -r requirements-prod.txt

# 5. Copy the entire project code into the container
COPY . /app

# 6. Ensure the application user owns the files/folders it will write to
RUN chown -R geoagriuser:geoagriuser /app

# 7. Collect Static Files (Gathers assets for Whitenoise)
# Running as root here is acceptable if permissions are fixed above
RUN python manage.py collectstatic --noinput

# -----------------------------------------------
# 🚀 SECURITY FIX: Switch to Non-Root User
# -----------------------------------------------
# Switch to the non-root user *before* running the application
USER geoagriuser
# -----------------------------------------------

# 8. Define Startup Command
# Uses your project name 'geoagri' and Gunicorn.
EXPOSE 8080
CMD gunicorn geoagri.wsgi:application --bind 0.0.0.0:$PORT