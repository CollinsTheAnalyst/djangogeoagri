from django.db import models

# Create your models here.
from django.contrib.gis.db import models
from django.contrib.auth.models import User

class FarmBoundary(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True)
    boundary = models.PolygonField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.owner.username}"
