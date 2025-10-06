from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.contrib.postgres.fields import JSONField  

class FarmBoundary(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255, default="Unknown")
    polygon = models.JSONField()  # stores coordinates
    area = models.FloatField(default=0.0)  # in m²
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner.username})"



# -------------------------
# Fertilizer Recommendation Models
# -------------------------

class Crop(models.Model):
    name = models.CharField(max_length=255)
    n_kg_per_ha = models.FloatField(default=0)
    p_kg_per_ha = models.FloatField(default=0)
    k_kg_per_ha = models.FloatField(default=0)


# -------------------------
# Fertilizer Models
# -------------------------

class Fertilizer(models.Model):
    """
    Represents a fertilizer with its N, P, K composition in percentage.
    """
    name = models.CharField(max_length=50, unique=True)
    n_percent = models.FloatField(default=0)  # Nitrogen content in %
    p_percent = models.FloatField(default=0)  # Phosphorus content in %
    k_percent = models.FloatField(default=0)  # Potassium content in %

    def __str__(self):
        return self.name


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
        unique_together = ('stage_name', 'fertilizer')  # same fertilizer can appear in multiple stages

    def __str__(self):
        return f"{self.stage_name} - {self.fertilizer.name}"
    



from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.contrib.postgres.fields import JSONField  

class FarmBoundary(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True)
    boundary = models.PolygonField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.owner.username}"


# -------------------------
# Fertilizer Recommendation Models
# -------------------------

class Crop(models.Model):
    name = models.CharField(max_length=255)
    n_kg_per_ha = models.FloatField(default=0)
    p_kg_per_ha = models.FloatField(default=0)
    k_kg_per_ha = models.FloatField(default=0)


# -------------------------
# Fertilizer Models
# -------------------------

class Fertilizer(models.Model):
    """
    Represents a fertilizer with its N, P, K composition in percentage.
    """
    name = models.CharField(max_length=50, unique=True)
    n_percent = models.FloatField(default=0)  # Nitrogen content in %
    p_percent = models.FloatField(default=0)  # Phosphorus content in %
    k_percent = models.FloatField(default=0)  # Potassium content in %

    def __str__(self):
        return self.name


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
        unique_together = ('stage_name', 'fertilizer')  # same fertilizer can appear in multiple stages

    def __str__(self):
        return f"{self.stage_name} - {self.fertilizer.name}"
    







