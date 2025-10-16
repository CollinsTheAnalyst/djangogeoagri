"""
URL configuration for geoagri project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings                
from django.conf.urls.static import static
from agrigeo import views


urlpatterns = [
    path('', include('agrigeo.urls')),
    path('blog/', include('blog.urls', namespace='blog')),          
    path('accounts/', include('accounts.urls')),  
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
    path('admin/', admin.site.urls),             
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    

]

# Serve uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
