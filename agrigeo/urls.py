from django.urls import path
from . import views

urlpatterns = [
    # Page views
    path('', views.home, name='home'),
    path('boundary-mapping/', views.boundary_mapping, name='boundary_mapping'),
    path('fertilizer-recommendation/', views.fertilizer_recommendation, name='fertilizer_recommendation'),
    path('ndvi-explorer/', views.ndvi_explorer, name='ndvi_explorer'),
    path('plant-disease/', views.plant_disease, name='plant_disease'),
    path('soil-nutrients/', views.soil_nutrients, name='soil_nutrients'),
    path('soil-taxonomy/', views.soil_taxonomic_groups, name='soil_taxonomic_groups'),

    # API endpoints
    path('save-boundary/', views.save_boundary, name='save_boundary'),
    path('get-counties/', views.get_counties, name='get_counties'),
    path('get-county-geometry/', views.get_county_geometry, name='get_county_geometry'),
    path('point-time-series/', views.point_time_series, name='point_time_series'),
    path('get-soil-data/', views.get_soil_data, name='get_soil_data'),

    # Soil taxonomy endpoints
    path('get-county-soils/', views.get_county_soils_with_names, name='get_county_soils_with_names'),
    path('get-soil-at-point/', views.get_soil_at_point, name='get_soil_at_point'),
    path('get-clipped-soils/', views.get_clipped_soils, name='get_clipped_soils'),

    # Plant disease
    path('predict/', views.predict_view, name='predict'),

    # Fertilizer Recommendation API
    path('fertilizer-api/<int:crop_id>/', views.get_crop_recommendation, name='get_crop_recommendation'),
]
