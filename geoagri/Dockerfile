# 1. Base Image: Use a Debian/Ubuntu-based Python image for apt-get access
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV DJANGO_SETTINGS_MODULE geoagri.settings

# 2. Install Geospatial System Dependencies
# Includes libraries from your apt.txt (gdal-bin, libgdal-dev) 
# plus standard geospatial requirements (GEOS/PROJ) and build tools.
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    git \
    build-essential \
    # Clean up to reduce final image size
    && rm -rf /var/lib/apt/lists/*

# 3. Apply Symlink Fix (from your apt.txt)
# This step is critical for GeoDjango to find the installed GDAL library.
RUN ln -s /usr/lib/x86_64-linux-gnu/libgdal.so /usr/lib/libgdal.so

# Set the working directory inside the container
WORKDIR /app

# 4. Copy and Install Python Dependencies
# We copy the requirements file separately to cache this layer
COPY requirements-prod.txt /app/
RUN pip install --no-cache-dir -r requirements-prod.txt

# 5. Copy the entire Django project code into the container
# The entire project structure, including the geoagri/ directory, is copied.
COPY . /app

# 6. Collect Static Files
# This is required to gather all static assets (including Leaflet.js, admin, etc.)
# and push them to the STATIC_ROOT directory/Cloudflare R2 bucket.
RUN python manage.py collectstatic --noinput

# 7. Expose Port and Define Startup Command
# Gunicorn is used as the production web server to run your WSGI application.
# The host (0.0.0.0) and port ($PORT) are required by PaaS platforms like Choreo.
# CRITICAL: We use 'geoagri.wsgi:application' based on your folder structure.
EXPOSE $PORT
CMD gunicorn geoagri.wsgi:application --bind 0.0.0.0:$PORT