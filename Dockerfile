# 1. Base Image: Use a Debian/Ubuntu-based Python image for apt-get access
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# 2. Install Geospatial System Dependencies
# From your apt.txt (gdal-bin, libgdal-dev) plus common geospatial libs.
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. Apply Symlink Fix
# CRITICAL for finding GDAL library
RUN ln -s /usr/lib/x86_64-linux-gnu/libgdal.so /usr/lib/libgdal.so

# Set the working directory inside the container
WORKDIR /app

# 4. Copy and Install Python Dependencies
# Use the production requirements file
COPY requirements-prod.txt /app/
RUN pip install --no-cache-dir -r requirements-prod.txt

# 5. Copy the entire project code into the container
COPY . /app

# 6. Collect Static Files (prepares files for Whitenoise serving)
RUN python manage.py collectstatic --noinput

# 7. Define Startup Command
# Uses your project name 'geoagri' and Gunicorn.
EXPOSE 8080
CMD gunicorn geoagri.wsgi:application --bind 0.0.0.0:$PORT