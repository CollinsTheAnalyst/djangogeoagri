from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


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

