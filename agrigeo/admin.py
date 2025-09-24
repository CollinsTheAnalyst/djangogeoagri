from django.contrib import admin
from .models import FarmBoundary

@admin.register(FarmBoundary)
class FarmBoundaryAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
