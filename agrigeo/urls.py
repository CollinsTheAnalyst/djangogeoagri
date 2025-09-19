from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('boundary-mapping/', views.boundary_mapping, name='boundary_mapping'),
    path('fertilizer-recommendation/', views.fertilizer_recommendation, name='fertilizer_recommendation'),
    path('ndvi-explorer/', views.ndvi_explorer, name='ndvi_explorer'),
    path('plant-disease/', views.plant_disease, name='plant_disease'),
    path('soil-nutrients/', views.soil_nutrients, name='soil_nutrients'),
    path('soil-taxonomy/', views.soil_taxonomic_groups, name='soil_taxonomic_groups'),

]



