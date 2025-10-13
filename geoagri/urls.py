"""
URL configuration for geoagri project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings                
from django.conf.urls.static import static       

urlpatterns = [
    path('', include('agrigeo.urls')),
    path('blog/', include('blog.urls')),          
    path('accounts/', include('accounts.urls')),  
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
    path('admin/', admin.site.urls),             
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

# Serve uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
