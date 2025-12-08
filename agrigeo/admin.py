from django.contrib import admin
from django.template.response import TemplateResponse
from blog.models import BlogPost
from django.db.models import Count, Sum

# Import your models
from .models import (
    Crop, Fertilizer, FertilizerStageMapping, CropApplication, FarmBoundary,
    Pest, Disease, SoilTaxonomy, CropPest, CropDisease,
    Nutrient, CropNutrientDeficiency  # <--- Added these imports
)

# --- Inline Configurations ---

class FertilizerStageMappingInline(admin.TabularInline):
    model = FertilizerStageMapping
    extra = 1
    autocomplete_fields = ("fertilizer",)

class CropApplicationInline(admin.TabularInline):
    model = CropApplication
    extra = 1

class CropPestInline(admin.TabularInline):
    model = CropPest
    extra = 1
    autocomplete_fields = ['pest']

class CropDiseaseInline(admin.TabularInline):
    model = CropDisease
    extra = 1
    autocomplete_fields = ['disease']

class CropNutrientDeficiencyInline(admin.StackedInline): # <--- Added Inline
    model = CropNutrientDeficiency
    extra = 1
    autocomplete_fields = ['nutrient']
    # Using StackedInline here because specific_damage/correction texts 
    # and images might be too wide for a table row.

# --- Admin Configurations ---

@admin.register(FarmBoundary)
class FarmBoundaryAdmin(admin.ModelAdmin):
    # Add 'area_display' to the list
    list_display = ("name", "owner", "area_display", "created_at") 
    list_filter = ("owner", "created_at")
    search_fields = ("name", "owner__username")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "area") # Make area readonly so no one edits it manually

    # Custom method to format the area nicely
    def area_display(self, obj):
        if obj.area:
            return f"{obj.area:.2f} acres"
        return "-"
    area_display.short_description = "Farm Size" # Sets the column header name

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ("name", "n_kg_per_ha", "p_kg_per_ha", "k_kg_per_ha")
    list_editable = ("n_kg_per_ha", "p_kg_per_ha", "k_kg_per_ha")
    search_fields = ("name",)
    # Added CropNutrientDeficiencyInline to the list below
    inlines = [CropApplicationInline, CropPestInline, CropDiseaseInline, CropNutrientDeficiencyInline]

@admin.register(Fertilizer)
class FertilizerAdmin(admin.ModelAdmin):
    list_display = ("name", "n_percent", "p_percent", "k_percent")
    search_fields = ("name",)
    inlines = [FertilizerStageMappingInline]

@admin.register(FertilizerStageMapping)
class FertilizerStageMappingAdmin(admin.ModelAdmin):
    list_display = ("stage_name", "fertilizer")
    list_filter = ("stage_name",)

@admin.register(CropApplication)
class CropApplicationAdmin(admin.ModelAdmin):
    list_display = ("crop", "num_applications", "description", "created_at")
    list_filter = ("crop",)
    
    def created_at(self, obj):
        return obj.created_at.strftime("%Y-%m-%d") if hasattr(obj, 'created_at') else "-"

@admin.register(Pest)
class PestAdmin(admin.ModelAdmin):
    list_display = ('name', 'scientific_name')
    search_fields = ('name',)

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'causal_agent')
    search_fields = ('name',)

@admin.register(Nutrient)  # <--- Registered Nutrient Model
class NutrientAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(SoilTaxonomy)
class SoilTaxonomyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# --- Custom Dashboard Logic ---

def custom_admin_dashboard(request):
    # Base context from Django Admin
    context = admin.site.each_context(request)
    
    # Agronomy Context Data
    context.update({
        'farm_count': FarmBoundary.objects.count(),
        'crop_count': Crop.objects.count(),
        'app_count': CropApplication.objects.count(),
        'pest_count': Pest.objects.count(),
        'disease_count': Disease.objects.count(),
        'fertilizer_count': Fertilizer.objects.count(),
        'soil_count': SoilTaxonomy.objects.count(),
        'nutrient_count': Nutrient.objects.count(), # <--- Added count
        
        # Recent Activities
        'latest_apps': CropApplication.objects.order_by('-id')[:5],
        'latest_posts': BlogPost.objects.order_by('-created_at')[:5],
        'blog_count': BlogPost.objects.count(),
    })
    
    return TemplateResponse(request, "admin/index.html", context)

admin.site.index = custom_admin_dashboard
admin.site.site_header = "GeoAgri Dashboard"
admin.site.index_title = "GeoAgri Insights"
admin.site.site_title = "GeoAgri Admin"