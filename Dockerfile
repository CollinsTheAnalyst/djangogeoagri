# ----------------------------------------------------
# 🚨 CACHE BUSTING LINE (CHANGE VALUE E.G., 20251121f) 🚨
ARG BUILD_DATE=20251121f
# ----------------------------------------------------

# 1. Base Image
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# 2. Install Geospatial System Dependencies
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

# 3. Setup Application Directory & Install Python
WORKDIR /app

# Install dependencies
COPY requirements-prod.txt /app/
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy project code
COPY . /app

# -----------------------------------------------
# 🚀 CRITICAL BUILD FIX: Set dummy DB values for collectstatic
# These values allow settings.py to load without crashing decouple.
# They are safely overwritten by Choreo secrets during runtime.
ENV DB_NAME=build_placeholder
ENV DB_USER=placeholder
ENV DB_PASSWORD=placeholder 
ENV DB_HOST=localhost
# -----------------------------------------------

ENV SECRET_KEY=build_secret_key_only

ENV EMAIL_HOST_USER=build_email_placeholder
ENV EMAIL_HOST_PASSWORD=build_email_password_placeholder


# 4. Collect Static Files (This step will now succeed)
RUN python manage.py collectstatic --noinput

# -----------------------------------------------
# 🚀 SECURITY FIX: Create User (Compliant UID 10001)
# -----------------------------------------------
# Create user with explicit UID and GID 10001 (Fixes CKV_CHOREO_1)
RUN groupadd -r geoagriuser -g 10001 && useradd -r -u 10001 -g geoagriuser geoagriuser
RUN chown -R 10001:10001 /app

# Switch to the required non-root user
USER 10001
# -----------------------------------------------

# 5. Define Startup Command
EXPOSE 8080
# 🚀 FIX: Run migrations AND hardcode port 8080 to satisfy Choreo
CMD python manage.py migrate && gunicorn geoagri.wsgi:application --bind 0.0.0.0:8080