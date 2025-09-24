from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.geos import GEOSGeometry
from .models import FarmBoundary
import json
import ee
import pandas as pd

# Initialize Google Earth Engine
ee.Initialize(project="ee-collinsmwiti98")

# -------------------------
# Page Views
# -------------------------
@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def boundary_mapping(request):
    return render(request, 'boundary_mapping.html')

@login_required
def fertilizer_recommendation(request):
    return render(request, 'fertilizer_recommendation.html')

@login_required
def ndvi_explorer(request):
    return render(request, 'ndvi_explorer.html')

@login_required
def plant_disease(request):
    return render(request, 'plant_disease.html')

@login_required
def soil_nutrients(request):
    return render(request, 'soil_nutrients.html')

@login_required
def soil_taxonomic_groups(request):
    return render(request, 'soil_taxonomy.html')


# -------------------------
# API Endpoints
# -------------------------
@login_required
@csrf_exempt
def save_boundary(request):
    if request.method == "POST":
        data = json.loads(request.body)
        geojson = data.get("geojson")
        name = data.get("name", "My Farm")

        # Convert GeoJSON to GEOSGeometry
        geom = GEOSGeometry(json.dumps(geojson["geometry"]))

        # Save boundary
        boundary = FarmBoundary.objects.create(
            owner=request.user,
            name=name,
            boundary=geom
        )
        return JsonResponse({"status": "success", "id": boundary.id})

    return JsonResponse({"status": "failed"}, status=400)


def get_counties(request):
    kenya_counties = ee.FeatureCollection("projects/ee-collinsmwiti98/assets/KenyaCounties")
    county_names = kenya_counties.aggregate_array("COUNTY").distinct().getInfo()
    return JsonResponse({"counties": county_names})


@login_required
def get_county_geometry(request):
    """
    Returns the GeoJSON geometry of a selected county.
    Expects GET parameter: ?county=<county_name>
    """
    county_name = request.GET.get("county")
    if not county_name:
        return JsonResponse({"error": "County name not provided"}, status=400)

    kenya_counties = ee.FeatureCollection("projects/ee-collinsmwiti98/assets/KenyaCounties")
    county_fc = kenya_counties.filter(ee.Filter.eq("COUNTY", county_name))
    county_feature = county_fc.first()

    if not county_feature:
        return JsonResponse({"error": "County not found"}, status=404)

    geojson = county_feature.geometry().getInfo()
    return JsonResponse({"geometry": geojson}, safe=False)


@login_required
@csrf_exempt
def point_time_series(request):
    """
    Returns NDVI/EVI time series for a user-selected point on the map.
    Expects JSON POST with lat, lng, metric, start_date, end_date
    """
    if request.method != "POST":
        return JsonResponse({"status": "failed", "error": "POST request required"}, status=400)

    body = json.loads(request.body)
    lat = body.get("lat")
    lng = body.get("lng")
    metric = body.get("metric", "NDVI")
    start_date = body.get("start_date")
    end_date = body.get("end_date")

    if not all([lat, lng, start_date, end_date]):
        return JsonResponse({"status": "failed", "error": "Missing parameters"}, status=400)

    point = ee.Geometry.Point([lng, lat])

    # MODIS NDVI/EVI collection
    collection = (
        ee.ImageCollection("MODIS/061/MOD13Q1")
        .filterBounds(point)
        .filterDate(start_date, end_date)
        .select([metric])
        .map(lambda img: img.multiply(0.0001).copyProperties(img, ['system:time_start']))
    )

    # Map a function to extract mean values (no getInfo here)
    def extract_feature(img):
        date = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
        mean = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=250,
            bestEffort=True
        ).get(metric)
        return ee.Feature(None, {'date': date, 'value': mean})

    ts_fc = collection.map(extract_feature)
    
    # Convert all features to a list and get info client-side
    try:
       # Convert EE FeatureCollection to a Python list of dicts
        ts_list = ts_fc.toList(ts_fc.size()).getInfo()  # fully resolves features
        ts_list = [f['properties'] for f in ts_list]   # extract native dicts

    except Exception as e:
        return JsonResponse({"status": "failed", "error": str(e)}, status=500)

    # Convert to DataFrame
    df = pd.DataFrame(ts_list)
    df = df.dropna(subset=['value'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    return JsonResponse(df.to_dict(orient="records"), safe=False)

