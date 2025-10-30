from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User

# -----------------------
# Farm Boundary Model
# -------------------------
class FarmBoundary(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True)
    
    # === ADD THESE TWO FIELDS ===
    location = models.CharField(max_length=255, blank=True, help_text="Search location/address provided by the user.")
    area = models.FloatField(default=0.0, help_text="Calculated area in acres.")
    # ============================
    
    boundary = models.PolygonField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.owner.username}"


# -------------------------
# Crop Model
# -------------------------
class Crop(models.Model):
    name = models.CharField(max_length=255)
    n_kg_per_ha = models.FloatField(default=0)
    p_kg_per_ha = models.FloatField(default=0)
    k_kg_per_ha = models.FloatField(default=0)

    def __str__(self):
        return self.name


# -------------------------
# Fertilizer Model
# -------------------------
class Fertilizer(models.Model):
    """
    Represents a fertilizer with its N, P, K composition in percentage.
    """
    name = models.CharField(max_length=50, unique=True)
    n_percent = models.FloatField(default=0)
    p_percent = models.FloatField(default=0)
    k_percent = models.FloatField(default=0)

    def __str__(self):
        return self.name


# -------------------------
# Fertilizer Stage Mapping Model
# -------------------------
class FertilizerStageMapping(models.Model):
    """
    Maps fertilizers to application stages (Planting, Top Dressing 1, Top Dressing 2, etc.)
    """
    STAGE_CHOICES = [
        ("Planting", "Planting"),
        ("Top Dressing 1", "Top Dressing 1"),
        ("Top Dressing 2", "Top Dressing 2"),
    ]

    stage_name = models.CharField(max_length=20, choices=STAGE_CHOICES)
    fertilizer = models.ForeignKey(Fertilizer, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('stage_name', 'fertilizer')

    def __str__(self):
        return f"{self.stage_name} - {self.fertilizer.name}"


# -------------------------
# Crop Application Model
# -------------------------
class CropApplication(models.Model):
    """Links a crop to its total number of fertilizer applications and description."""
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    num_applications = models.IntegerField(default=1)
    description = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        # Optional: auto-generate description based on number of applications
        stage_names = ["Planting", "Top Dressing 1", "Top Dressing 2"]
        self.description = " + ".join(stage_names[:self.num_applications])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.crop.name} ({self.description})"
    

