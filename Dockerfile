# 1. Base image
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 2. Create non-root user
RUN groupadd -r geoagriuser && useradd --no-log-init -r -g geoagriuser geoagriuser

# 3. System dependencies (root)
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/lib/x86_64-linux-gnu/libgdal.so /usr/lib/libgdal.so

# 4. Set working directory
WORKDIR /app

# 5. Copy requirements and install as root (pip can run as non-root too, but often safer here)
COPY requirements-prod.txt /app/
RUN pip install --no-cache-dir -r requirements-prod.txt

# 6. Copy project files
COPY . /app

# 7. Switch to non-root **before any app commands**
USER geoagriuser

# 8. Fix permissions (just in case)
RUN chown -R geoagriuser:geoagriuser /app

# 9. Collect static as non-root (optional: can still run as root if needed)
RUN python manage.py collectstatic --noinput

# 10. Expose port
EXPOSE 8080

# 11. Run app
CMD ["gunicorn", "geoagri.wsgi:application", "--bind", "0.0.0.0:8080"]
