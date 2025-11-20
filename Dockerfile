# ... (Lines 1-3: Base Image, ENV vars) ...
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# -----------------------------------------------
# 🚀 SECURITY FIX: Create Non-Root User
# -----------------------------------------------
# Create a non-root user and group
RUN groupadd -r geoagriuser && useradd --no-log-init -r -g geoagriuser geoagriuser
# Set necessary ownership for core app directories
RUN mkdir -p /app/staticfiles && chown -R geoagriuser:geoagriuser /app
# -----------------------------------------------

# 2. Install Geospatial System Dependencies
# ... (This section remains unchanged) ...
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. Apply Symlink Fix
RUN ln -s /usr/lib/x86_64-linux-gnu/libgdal.so /usr/lib/libgdal.so

# Set the working directory inside the container
WORKDIR /app

# 4. Copy and Install Python Dependencies (Ensure these steps run after user creation)
COPY requirements-prod.txt /app/
RUN pip install --no-cache-dir -r requirements-prod.txt

# 5. Copy the entire project code into the container
COPY . /app

# 6. Collect Static Files (manage.py uses the app user)
RUN python manage.py collectstatic --noinput

# -----------------------------------------------
# 🚀 SECURITY FIX: Switch to Non-Root User
# -----------------------------------------------
# Switch to the non-root user before running the application
USER geoagriuser
# -----------------------------------------------

# 7. Define Startup Command
EXPOSE 8080
CMD gunicorn geoagri.wsgi:application --bind 0.0.0.0:$PORT