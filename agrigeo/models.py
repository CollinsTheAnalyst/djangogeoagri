from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.contrib.postgres.fields import JSONField

# -----------------------
# Farm Boundary Model
# -------------------------
class FarmBoundary(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True)
    boundary = models.PolygonField()
    # 🆕 ADD THIS FIELD:
    area = models.FloatField(null=True, blank=True, help_text="Area in acres") 
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
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    num_applications = models.IntegerField(default=1)
    description = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        stage_names = ["Planting", "Top Dressing 1", "Top Dressing 2"]
        self.description = " + ".join(stage_names[:self.num_applications])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.crop.name} ({self.description})"


# ==========================================
# 🚀 1. NEW: Pests and Diseases (Linked to Crops)
# ==========================================

class Pest(models.Model):
    name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=100, blank=True)
    description = models.TextField(help_text="General description and identification of the pest")
    control_methods = models.TextField(help_text="General control methods")
    image = models.ImageField(upload_to='pests/', blank=True, null=True)

    def __str__(self):
        return self.name

class Disease(models.Model):
    name = models.CharField(max_length=100)
    causal_agent = models.CharField(max_length=100, help_text="e.g., Fungal, Bacterial, Viral")
    description = models.TextField(help_text="General description of the disease")
    treatment = models.TextField(help_text="General treatment options")
    image = models.ImageField(upload_to='diseases/', blank=True, null=True)

    def __str__(self):
        return self.name
    
# 3. The Link: Crop <-> Pest
class CropPest(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='crop_pests')
    pest = models.ForeignKey(Pest, on_delete=models.CASCADE, related_name='pest_occurrences')
    
    # Specifics for THIS crop
    specific_damage = models.TextField(help_text="How does this pest specifically damage this crop?")
    
    
    class Meta:
        unique_together = ('crop', 'pest') # Prevent adding the same pest to a crop twice
        verbose_name = "Pest affecting Crop"

    def __str__(self):
        return f"{self.pest.name} on {self.crop.name}"

# 4. The Link: Crop <-> Disease
class CropDisease(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='crop_diseases')
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='disease_occurrences')
    
    # Specifics for THIS crop
    specific_damage = models.TextField(help_text="Symptoms specific to this crop")
    
    class Meta:
        unique_together = ('crop', 'disease')
        verbose_name = "Disease affecting Crop"

    def __str__(self):
        return f"{self.disease.name} on {self.crop.name}"
    
# 5. Base Entity: Nutrient
class Nutrient(models.Model):
    """
    Represents a specific nutrient (e.g., Nitrogen, Phosphorus, Zinc).
    """
    name = models.CharField(max_length=50, unique=True, help_text="E.g., Nitrogen (N), Phosphorus (P)")
    
    def __str__(self):
        return self.name

# 6. The Link: Crop <-> Nutrient (Deficiency & Correction)
class CropNutrientDeficiency(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='nutrient_deficiencies')
    nutrient = models.ForeignKey(Nutrient, on_delete=models.CASCADE, related_name='crop_deficiencies')
    
    # Specifics for THIS crop
    deficiency_symptoms = models.TextField(help_text="Visual symptoms of this deficiency on the crop.")
    symptom_image = models.ImageField(
        upload_to='nutrient_deficiencies/', 
        blank=True, 
        null=True, 
        help_text="Upload a picture of the deficiency symptoms"
    )
    correction = models.TextField(help_text="Methods or fertilizers to correct this deficiency.")

    class Meta:
        unique_together = ('crop', 'nutrient') # Ensures unique pairing
        verbose_name = "Crop Nutrient Deficiency"
        verbose_name_plural = "Crop Nutrient Deficiencies"

    def __str__(self):
        return f"{self.nutrient.name} deficiency in {self.crop.name}"

# ==========================================
# 🚀 2. NEW: Soil Taxonomy (Dynamic Reports)
# ==========================================

class SoilTaxonomy(models.Model):
    """
    Stores soil type summaries and reports dynamically.
    Replaces hardcoded logic so you can upload PDFs via Admin.
    """
    name = models.CharField(max_length=100, unique=True, help_text="e.g., Acric Ferralsols")
    
    # The Summary Text
    summary = models.TextField(help_text="A brief agronomic summary of this soil type.")
    
    # The PDF Report (No more hardcoded paths!)
    pdf_report = models.FileField(upload_to='soil_reports/', blank=True, null=True, help_text="Upload the detailed PDF report here.")
    
    image = models.ImageField(upload_to='soil_images/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Soil Taxonomies"

    def __str__(self):
        return self.name