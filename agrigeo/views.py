from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.geos import GEOSGeometry
from .models import FarmBoundary
from .soil_summaries import soil_summaries
from .legend import soil_code_guide
import json
import ee
import pandas as pd
import io
import numpy as np
from django.core.files.uploadedfile import InMemoryUploadedFile
from tensorflow.keras.preprocessing import image
import os
from django.conf import settings
from tensorflow.keras.models import load_model
from .models import Crop

MODEL_PATH = os.path.join(settings.BASE_DIR, "agrigeo", "potatoes.h5")

try:
    MODEL = load_model(MODEL_PATH, compile=False)
    print("MODEL:", MODEL)

    
except Exception as e:
    MODEL = None
    print("❌ Error loading model:", e)


# Initialize Google Earth Engine
ee.Initialize(project="ee-collinsmwiti98")



# -------------------------
# Page Views
# -------------------------

def home(request):
    return render(request, 'home.html')   # Public landing page


@login_required
def boundary_mapping(request):
    return render(request, 'boundary_mapping.html')

@login_required
def fertilizer_recommendation(request):
    crops = Crop.objects.all().order_by("name")  # fetch all crops
    return render(request, 'fertilizer_recommendation.html', {"crops": crops})


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
# Farm Boundary Endpoints
# -------------------------
@login_required
@csrf_exempt
def save_boundary(request):
    if request.method != "POST":
        return JsonResponse({"status": "failed", "error": "POST request required"}, status=400)
    try:
        data = json.loads(request.body)
        geojson = data.get("geojson")
        name = data.get("name", "My Farm")

        geom = GEOSGeometry(json.dumps(geojson["geometry"]))
        boundary = FarmBoundary.objects.create(owner=request.user, name=name, boundary=geom)
        return JsonResponse({"status": "success", "id": boundary.id})
    except Exception as e:
        return JsonResponse({"status": "failed", "error": str(e)}, status=400)


# -------------------------
# Counties / Geometry
# -------------------------
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
        county_feature = kenya_counties.filter(ee.Filter.eq("COUNTY", county_name)).first()
        if not county_feature:
            return JsonResponse({"error": "County not found"}, status=404)
        geojson = county_feature.geometry().getInfo()
        return JsonResponse({"geometry": geojson}, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# -------------------------
# NDVI / Time Series
# -------------------------
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
            mean = img.reduceRegion(ee.Reducer.mean(), point, scale=250, bestEffort=True).get(metric)
            return ee.Feature(None, {'date': date, 'value': mean})

        ts_list = [f['properties'] for f in collection.map(extract_feature).toList(collection.size()).getInfo()]
        df = pd.DataFrame(ts_list).dropna(subset=['value'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        return JsonResponse(df.to_dict(orient="records"), safe=False)
    except Exception as e:
        return JsonResponse({"status": "failed", "error": str(e)}, status=500)


# -------------------------
# Soil Nutrients
# -------------------------
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

        nutrient_code_map = {
            "N": "N", "P": "P", "K": "K", "Ca": "Ca", "Mg": "Mg",
            "C": "Carbon", "Fe": "Fe", "Zn": "Zn", "CEC": "CEC", "pH": "pH"
        }

        results = {}
        for nut in nutrients:
            ee_key = nutrient_code_map.get(nut)
            if ee_key and ee_key in soil_layers:
                try:
                    img = soil_layers[ee_key]
                    val_dict = img.reduceRegion(ee.Reducer.mean(), point, scale=250, bestEffort=True).getInfo()
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


# -------------------------
# Soil Taxonomy Endpoints
# -------------------------
@login_required
def get_county_soils_with_names(request):
    """
    Returns soil codes and readable names for a county.
    """
    county_name = request.GET.get("county")
    if not county_name:
        return JsonResponse({"error": "County name not provided"}, status=400)

    try:
        kenya_counties = ee.FeatureCollection("projects/ee-collinsmwiti98/assets/KenyaCounties")
        kenya_soils = ee.FeatureCollection("projects/ee-collinsmwiti98/assets/kenyasoils_styled")
        county_fc = kenya_counties.filter(ee.Filter.eq("COUNTY", county_name))
        county_soils = kenya_soils.filterBounds(county_fc).select(['DOMSOI'])

        soil_codes = county_soils.aggregate_array("DOMSOI").distinct().getInfo()
        soil_names = [soil_code_guide.get(code, "Unknown") for code in soil_codes]

        return JsonResponse({
            "county": county_name,
            "soil_codes": soil_codes,
            "soil_names": soil_names
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@csrf_exempt
def get_soil_at_point(request):
    """
    Returns soil code, name, and summary at a clicked point.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=400)
    try:
        body = json.loads(request.body)
        lat = body.get("lat")
        lng = body.get("lng")
        if not all([lat, lng]):
            return JsonResponse({"error": "Missing lat/lng"}, status=400)

        point = ee.Geometry.Point([lng, lat])
        kenya_soils = ee.FeatureCollection("projects/ee-collinsmwiti98/assets/kenyasoils_styled")
        selected_soil = kenya_soils.filterBounds(point).first()
        if not selected_soil:
            return JsonResponse({"error": "No soil polygon found at this point"}, status=404)

        soil_code = selected_soil.get("DOMSOI").getInfo()
        soil_name = soil_code_guide.get(soil_code, "Unknown")
        summary = soil_summaries.get(soil_name, "No summary available")

        return JsonResponse({
            "soil_code": soil_code,
            "soil_name": soil_name,
            "summary": summary
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def get_clipped_soils(request):
    """
    Returns a county-clipped soil GeoJSON with DOMSOI property for Leaflet.
    """
    county_name = request.GET.get("county")
    if not county_name:
        return JsonResponse({"error": "County name not provided"}, status=400)
    
    try:
        kenya_counties = ee.FeatureCollection("projects/ee-collinsmwiti98/assets/KenyaCounties")
        kenya_soils = ee.FeatureCollection("projects/ee-collinsmwiti98/assets/kenyasoils_styled")
        
        county_fc = kenya_counties.filter(ee.Filter.eq("COUNTY", county_name))
        county_soils = kenya_soils.filterBounds(county_fc).select(['DOMSOI', 'fillColor', 'fillOpacity', 'strokeColor', 'strokeWidth'])

        # Get features
        features = county_soils.getInfo()['features']
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": f['geometry'],
                    "properties": {
                        "DOMSOI": f['properties'].get('DOMSOI'),
                        "fillColor": f['properties'].get('fillColor', '#cccccc'),
                        "fillOpacity": f['properties'].get('fillOpacity', 0.7),
                        "strokeColor": f['properties'].get('strokeColor', '#000000'),
                        "strokeWidth": f['properties'].get('strokeWidth', 1),
                    }
                } for f in features
            ]
        }

        return JsonResponse(geojson, safe=False)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
## Plant disease

@csrf_exempt
def predict_view(request):
    print("=== predict_view called ===")
    print("Request method:", request.method)
    print("FILES:", request.FILES)
    print("POST data:", request.POST)
    
    if request.method == "POST":
        file: InMemoryUploadedFile = request.FILES.get("file")
        crop = request.POST.get("crop")
        print("Received file:", file)
        print("Received crop:", crop)

        if not file:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        try:
            # Read the image file into PIL
            img = image.load_img(file, target_size=(224, 224))  # resize to match model input
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0) / 255.0  # normalize

            # Run prediction
            preds = MODEL.predict(img_array)
            predicted_class = int(np.argmax(preds[0]))
            confidence = float(np.max(preds[0]))

            # Dummy mapping (replace with your actual class labels)
            class_labels = ["Healthy", "Disease A", "Disease B"]
            disease = class_labels[predicted_class] if predicted_class < len(class_labels) else "Unknown"

            # Example response
            return JsonResponse({
                "prediction": disease,
                "confidence": confidence,
                "stage": "Early",   # placeholder, can refine later
                "treatment": "Apply recommended fungicide",  # placeholder
            })
        except Exception as e:
            print("Prediction error:", e)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=405)



# -------------------------
# Fertilizer Recommendation page
@login_required
def get_crop_recommendation(request, crop_id):
    try:
        crop = Crop.objects.get(id=crop_id)
        data = {
            "id": crop.id,
            "crop": crop.name,
            "N": crop.n_kg_per_ha,
            "P": crop.p_kg_per_ha,
            "K": crop.k_kg_per_ha,
            "unit": "kg/ha"
        }
        return JsonResponse(data)
    except Crop.DoesNotExist:
        return JsonResponse({"error": "Crop not found"}, status=404)


    


