"""
Django settings for geoagri project.
"""
import os
from pathlib import Path
import platform
import ctypes.util
from .jazzmin_config import JAZZMIN_SETTINGS, JAZZMIN_UI_TWEAKS

# --- NEW IMPORTS FOR DEPLOYMENT (MANDATORY) ---
from decouple import config
import dj_database_url
# --- END NEW IMPORTS ---


if platform.system() == "Windows":
    # Local (conda)
    GDAL_LIBRARY_PATH = os.path.join(
        os.environ.get('CONDA_PREFIX', ''), 'Library', 'bin', 'gdal310.dll'
    )
else:
    # Linux (Render, Ubuntu/Debian)
    gdal_lib = ctypes.util.find_library("gdal")
    if gdal_lib:
        GDAL_LIBRARY_PATH = gdal_lib
    else:
        GDAL_LIBRARY_PATH = "/usr/lib/x86_64-linux-gnu/libgdal.so"  # fallback


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


ALLOWED_HOSTS = ["*"]


INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'leaflet',
    'agrigeo',
    'accounts',
    "django_plotly_dash.apps.DjangoPlotlyDashConfig",
    "dpd_static_support",
    "channels",
    'blog',
    'ckeditor', # Using standard ckeditor apps
    'ckeditor_uploader', # Using standard ckeditor apps
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django_plotly_dash.middleware.BaseMiddleware",
    "django_plotly_dash.middleware.ExternalRedirectionMiddleware",
]

ROOT_URLCONF = 'geoagri.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'geoagri.wsgi.application'
ASGI_APPLICATION = "geoagri.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}


# ----------------------------------------------------
# 🚀 Database Configuration (Handles Local or Cloud URL)
# ----------------------------------------------------

# 1. Check for the cloud-provided DATABASE_URL environment variable first.
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True  # Recommended for secure cloud connections
        )
    }
    # CRITICAL: Re-apply the GeoDjango PostGIS engine after parsing the URL
    DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'
else:
    # 2. Fallback: Use the original decouple configuration for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }


SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC' # Changed to UTC for robust cloud behavior

USE_I18N = True

USE_TZ = True


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# URL for static files
STATIC_URL = '/static/'

# Folder where collectstatic will copy files for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # separate folder

# Additional folders where Django will look for static files in development
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # your dev static files (js, css, images)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestFilesStorage' # Changed to CompressedManifestFilesStorage


# settings.py
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# Leaflet configuration
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (-1.0, 37.0),
    'DEFAULT_ZOOM': 8,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 18,
    'TILES': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", cast=int, default=587)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool, default=True)

EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
CKEDITOR_UPLOAD_PATH = "uploads/"

# CKEditor Configuration (Updated for ckeditor/ckeditor_uploader apps)
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline', '-', 'RemoveFormat'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent'],
            ['Link', 'Unlink', 'Anchor'],
            ['Image', 'Table', 'HorizontalRule', 'Smiley', 'SpecialChar'],
            ['Styles', 'Format', 'Font', 'FontSize'],
            ['TextColor', 'BGColor'],
            ['Maximize', 'ShowBlocks'],
        ],
        'extraPlugins': 'codesnippet',
    }
}


# =======================================================
# 🚀 DJANGO PLOTLY DASH CONFIGURATION (for Bootstrap compatibility)
# =======================================================
DJANGO_PLOTLY_DASH = {
    'served_externally': True,
    'external_js': None,
    'external_css': None,
    'external_dependencies': {
        'jquery_support': False,
        'bootstrap_css': None,
        'bootstrap_js': None
    }
}