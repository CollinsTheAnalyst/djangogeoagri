from django.contrib import admin
from .models import Crop, Fertilizer, FertilizerStageMapping, CropApplication, FarmBoundary
from django.template.response import TemplateResponse
from .models import Crop, CropApplication, FarmBoundary
from django.contrib import admin
from django.contrib import admin
from blog.models import BlogPost




# --- Inline Configurations ---
class FertilizerStageMappingInline(admin.TabularInline):
    model = FertilizerStageMapping
    extra = 1
    autocomplete_fields = ("fertilizer",)


class CropApplicationInline(admin.TabularInline):
    model = CropApplication
    extra = 1
    autocomplete_fields = ("crop",)


# --- Admin Configurations ---
@admin.register(FarmBoundary)
class FarmBoundaryAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    list_filter = ("owner", "created_at")
    search_fields = ("name", "owner__username")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ("name", "n_kg_per_ha", "p_kg_per_ha", "k_kg_per_ha")
    list_editable = ("n_kg_per_ha", "p_kg_per_ha", "k_kg_per_ha")
    search_fields = ("name",)
    ordering = ("name",)
    inlines = [CropApplicationInline]


@admin.register(Fertilizer)
class FertilizerAdmin(admin.ModelAdmin):
    list_display = ("name", "n_percent", "p_percent", "k_percent")
    list_editable = ("n_percent", "p_percent", "k_percent")
    search_fields = ("name",)
    ordering = ("name",)
    inlines = [FertilizerStageMappingInline]


@admin.register(FertilizerStageMapping)
class FertilizerStageMappingAdmin(admin.ModelAdmin):
    list_display = ("stage_name", "fertilizer", "n_percent", "p_percent", "k_percent")
    list_filter = ("stage_name",)
    search_fields = ("fertilizer__name",)
    
    def n_percent(self, obj):
        return obj.fertilizer.n_percent
    def p_percent(self, obj):
        return obj.fertilizer.p_percent
    def k_percent(self, obj):
        return obj.fertilizer.k_percent


@admin.register(CropApplication)
class CropApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "crop_name", "num_applications", "description")
    list_editable = ("num_applications",)
    search_fields = ("crop__name", "description")

    def crop_name(self, obj):
        return obj.crop.name
    crop_name.admin_order_field = "crop"
    crop_name.short_description = "Crop"



def custom_admin_dashboard(request):
    context = dict(
        admin.site.each_context(request),
        farm_count=FarmBoundary.objects.count(),
        crop_count=Crop.objects.count(),
        app_count=CropApplication.objects.count(),
        blog_count=BlogPost.objects.count(),
        latest_posts=BlogPost.objects.order_by('-created_at')[:5],
    )
    return TemplateResponse(request, "admin/index.html", context)


admin.site.index = custom_admin_dashboard
admin.site.site_header = "🌾 GeoAgri Dashboard"
admin.site.index_title = "GeoAgri Insights"
admin.site.site_title = "GeoAgri Admin"


