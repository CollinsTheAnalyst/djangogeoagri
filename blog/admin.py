from django.contrib import admin
from .models import BlogPost, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name",)

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "category", "author", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("title", "content")
