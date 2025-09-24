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
        try:
            data = json.loads(request.body)
            geojson = data.get("geojson")
            name = data.get("name", "My Farm")

            geom = GEOSGeometry(json.dumps(geojson["geometry"]))

            boundary = FarmBoundary.objects.create(
                owner=request.user,
                name=name,
                boundary=geom
            )
            return JsonResponse({"status": "success", "id": boundary.id})
        except Exception as e:
            return JsonResponse({"status": "failed", "error": str(e)}, status=400)

    return JsonResponse({"status": "failed", "error": "POST request required"}, status=400)


@login_required
def get_counties(request):
    try:
        kenya_counties = ee.FeatureCollection("projects/ee-collinsmwiti98/assets/KenyaCounties")
        county_names = kenya_counties.aggregate_array("COUNTY").distinct().getInfo()
        return JsonResponse({"counties": county_names})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def get_county_geometry(request):
    county_name = request.GET.get("county")
    if not county_name:
        return JsonResponse({"error": "County name not provided"}, status=400)
    try:
        kenya_counties = ee.FeatureCollection("projects/ee-collinsmwiti98/assets/KenyaCounties")
        county_fc = kenya_counties.filter(ee.Filter.eq("COUNTY", county_name))
        county_feature = county_fc.first()

        if not county_feature:
            return JsonResponse({"error": "County not found"}, status=404)

        geojson = county_feature.geometry().getInfo()
        return JsonResponse({"geometry": geojson}, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@csrf_exempt
def point_time_series(request):
    if request.method != "POST":
        return JsonResponse({"status": "failed", "error": "POST request required"}, status=400)
    try:
        body = json.loads(request.body)
        lat = body.get("lat")
        lng = body.get("lng")
        metric = body.get("metric", "NDVI")
        start_date = body.get("start_date")
        end_date = body.get("end_date")

        if not all([lat, lng, start_date, end_date]):
            return JsonResponse({"status": "failed", "error": "Missing parameters"}, status=400)

        point = ee.Geometry.Point([lng, lat])

        collection = (
            ee.ImageCollection("MODIS/061/MOD13Q1")
            .filterBounds(point)
            .filterDate(start_date, end_date)
            .select([metric])
            .map(lambda img: img.multiply(0.0001).copyProperties(img, ['system:time_start']))
        )

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

        ts_list = ts_fc.toList(ts_fc.size()).getInfo()
        ts_list = [f['properties'] for f in ts_list]

        df = pd.DataFrame(ts_list)
        df = df.dropna(subset=['value'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        return JsonResponse(df.to_dict(orient="records"), safe=False)

    except Exception as e:
        return JsonResponse({"status": "failed", "error": str(e)}, status=500)


@login_required
@csrf_exempt
def get_soil_data(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=400)
    try:
        body = json.loads(request.body)
        lat = body.get("lat")
        lng = body.get("lng")
        nutrients = body.get("nutrients", [])

        if not all([lat, lng, nutrients]):
            return JsonResponse({"error": "Missing parameters"}, status=400)

        point = ee.Geometry.Point([lng, lat])

        soil_layers = {
            "pH": ee.Image("ISDASOIL/Africa/v1/ph").select('mean_0_20').divide(10),
            "N": ee.Image("ISDASOIL/Africa/v1/nitrogen_total").select('mean_0_20').divide(100).exp().subtract(1),
            "P": ee.Image("ISDASOIL/Africa/v1/phosphorus_extractable").select('mean_0_20').divide(10).exp().subtract(1),
            "K": ee.Image("ISDASOIL/Africa/v1/potassium_extractable").select('mean_0_20').divide(10).exp().subtract(1),
            "Ca": ee.Image("ISDASOIL/Africa/v1/calcium_extractable").select('mean_0_20').divide(10).exp().subtract(1),
            "Mg": ee.Image("ISDASOIL/Africa/v1/magnesium_extractable").select('mean_0_20').divide(10).exp().subtract(1),
            "CEC": ee.Image("ISDASOIL/Africa/v1/cation_exchange_capacity").select('mean_0_20').divide(10).exp().subtract(1),
            "Fe": ee.Image("ISDASOIL/Africa/v1/iron_extractable").select('mean_0_20').divide(10).exp().subtract(1),
            "Carbon": ee.Image("ISDASOIL/Africa/v1/carbon_organic").select('mean_0_20').divide(10).exp().subtract(1),
            "Zn": ee.Image("ISDASOIL/Africa/v1/zinc_extractable").select('mean_0_20').divide(10).exp().subtract(1),
        }

        # Map nutrient codes from client to soil_layers keys
        nutrient_code_map = {
            "N": "N",
            "P": "P",
            "K": "K",
            "Ca": "Ca",
            "Mg": "Mg",
            "C": "Carbon",  # fix for client sending "C"
            "Fe": "Fe",
            "Zn": "Zn",
            "CEC": "CEC",
            "pH": "pH"
        }

        results = {}
        for nut in nutrients:
            ee_key = nutrient_code_map.get(nut)
            if ee_key and ee_key in soil_layers:
                try:
                    img = soil_layers[ee_key]
                    val_dict = img.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=point,
                        scale=250,
                        bestEffort=True
                    ).getInfo()
                    band_name = img.bandNames().get(0).getInfo()
                    val = val_dict.get(band_name)
                    results[nut] = round(val, 2) if val is not None else "No data"
                except Exception as e:
                    results[nut] = f"Error: {str(e)}"
            else:
                results[nut] = "Invalid nutrient"

        return JsonResponse(results)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


