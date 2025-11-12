from django.urls import path
from . import views

urlpatterns = [
    # 🌍 General Page Views
    path('', views.home, name='home'),
    path('boundary-mapping/', views.boundary_mapping, name='boundary_mapping'),
    path('fertilizer-recommendation/', views.fertilizer_recommendation, name='fertilizer_recommendation'),
    path('plant-disease/', views.plant_disease, name='plant_disease'),
    path('contact/', views.contact, name='contact'),

    # 🗺️ Selection Views (These are now REMOVED as they are redundant)
    # The Generic Analysis Views below will now handle the initial navigation.
    # path('ndvi-selection/', views.ndvi_selection_view, name='ndvi_selection'), 
    # path('soil-nutrients-selection/', views.soil_nutrients_selection, name='soil_nutrients_selection'), 
    # path('soil-taxonomy-selection/', views.soil_taxonomy_selection, name='soil_taxonomy_selection'), 

    # 📊 Generic Analysis Views (Restored to be directly navigable)
    # These views should render the map/interface but without a specific farm pre-loaded.
    path('ndvi-explorer/', views.ndvi_explorer, name='ndvi_explorer'),
    path('soil-nutrients/', views.soil_nutrients, name='soil_nutrients'),
    path('soil-taxonomy/', views.soil_taxonomic_groups, name='soil_taxonomic_groups'),

    # 📊 Dynamic Analysis Views (Still required for specific farm analysis)
    # These views are linked from the map/farm list and pre-load data for a specific farm_id.
    path('farm-details/<int:farm_id>/ndvi/', views.ndvi_explorer, name='farm_ndvi_explorer'),
    path('farm-details/<int:farm_id>/soil-nutrients/', views.soil_nutrients, name='farm_soil_nutrients'),
    path('farm-details/<int:farm_id>/soil-taxonomy/', views.soil_taxonomic_groups, name='farm_soil_taxonomic_groups'),
    
    # ⚙️ API Endpoints
    path('save-boundary/', views.save_boundary, name='save_boundary'),
    path('get-counties/', views.get_counties, name='get_counties'),
    path('get-county-geometry/', views.get_county_geometry, name='get_county_geometry'),
    path('point-time-series/', views.point_time_series, name='point_time_series'),
    path('get-soil-data/', views.get_soil_data, name='get_soil_data'),

    # Soil Taxonomy Endpoints
    path('get-county-soils/', views.get_county_soils_with_names, name='get_county_soils_with_names'),
    path('get-soil-at-point/', views.get_soil_at_point, name='get_soil_at_point'),
    path('get-clipped-soils/', views.get_clipped_soils, name='get_clipped_soils'),
    path('reverse-geocode/', views.reverse_geocode, name='reverse_geocode'),
    path('soilreport/<str:soil_code>/download/', views.download_soil_report, name='download_soil_report'),

    # Plant Disease
    path('predict/', views.predict_view, name='predict'),
    
    # Other API Endpoints
    path('fertilizer-api/<int:crop_id>/', views.get_crop_recommendation, name='get_crop_recommendation'),
    path('save-farm-boundary/', views.save_farm_boundary, name='save_farm_boundary'),
    path('crop-applications/<int:crop_id>/', views.crop_applications_api, name='crop_applications_api'),
]