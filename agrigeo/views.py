# views.py

import json
import os
import numpy as np
import pandas as pd
import requests
from io import BytesIO

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.templatetags.static import static
from django.conf import settings

from django.core.serializers.json import DjangoJSONEncoder

from django.contrib.gis.geos import GEOSGeometry

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

import ee

from .models import FarmBoundary, Crop, FertilizerStageMapping
from .soil_summaries import soil_summaries
from .legend import soil_code_guide

from django.http import FileResponse, Http404
from .models import CropApplication, Crop


# ===========================
# Soil Reports Mapping (Global)
# ===========================
SOIL_REPORTS = {
    "Fr": "Acric Ferralsols.pdf",
    "Af": "Ferric Acrisols.pdf",
    "Vc": "Chromic Vertisols.pdf",
    "Vp": "Pellic Vertisols.pdf",
    "Bd": "Dystric Cambisols.pdf",
    "Ne": "Eutric Nitisols.pdf",
    "Nh": "Humic Nitisols.pdf",
    "Nd": "Dystric Nitisols.pdf",
    "Be": "Eutric Cambisols.pdf",
    "We": "Eutric Planosols.pdf",
    "Wf": "Ferralic Planosols.pdf",
    "Fo": "Orthic Ferralsols.pdf",
    "Fp": "plinthic Ferralsols.pdf",
    "Lf": "Ferric Lithosols.pdf",
    "Qf": "FerricArenosols.pdf",
    "Lg": "Gleyic Lithosols.pdf", 
    "Gh": "Haplic Chernozems.pdf",
    "Bh": "Humic Cambisols.pdf",
    "Wh": "Humic Planosols.pdf",
    "Ql": "LuvicArenosols.pdf",
    "Tm": "Mollic Andosols.pdf",
    "Gm": "Mollic Gleysols.pdf",
    "To": "Orthic Andosols.pdf",
    "Of": "Orthic Ferralsols.pdf",
    "Zo": "Orthic Solonchanks.pdf",
    "Fp": "plinthic Ferralsols.pdf",
    "Re": "Eutric Regosols.pdf",
    "G":  "GLEYSOLS.pdf",
    "I":  "Lithosols.pdf",
    "Jc": "Calcaric Fluviosols.pdf",
    "Rc": "Calcaric Regosols.pdf",
    "Xk": "Calcic Xerosols.pdf",
    "Yk": "Calcic Yermosols.pdf",
    "X": "XEROSOLS.pdf",
    "Yh":"Haplic Yermosols.pdf",
}


# ===========================
# Initialize External Services
# ===========================
# Initialize Google Earth Engine
try:
    ee.Initialize(project="ee-collinsmwiti98")
except Exception as e:
    print("❌ Error initializing Earth Engine:", e)


# ===========================
# Load Plant Disease Models
# ===========================
MODEL_DIR = os.path.join(settings.BASE_DIR, "agrigeo", "models")

MODEL_FILES = {
    "potato": {"file": "potato_2.12.h5", "input_size": (256, 256)},
    "maize": {"file": "Maize_disease_model_2.20.h5", "input_size": (224, 224)},
    "wheat": {"file": "Wheat_disease_model_2.20.h5", "input_size": (224, 224)},
    "tomato": {"file": "Tomato_disease_model_2.20.h5", "input_size": (224, 224)},
}

MODELS = {}
for crop_name, info in MODEL_FILES.items():
    path = os.path.join(MODEL_DIR, info["file"])
    try:
        model = load_model(path, compile=False)
        MODELS[crop_name] = {
            "model": model,
            "input_size": info["input_size"]
        }
        print(f"✅ {crop_name} model loaded from {info['file']} with input size {info['input_size']}")
    except Exception as e:
        MODELS[crop_name] = None
        print(f"❌ Error loading {crop_name} model: {e}")



# ===========================
# Public Views
# ===========================
def home(request):
    """Public landing page"""
    return render(request, 'home.html')


# ===========================
# Authenticated Page Views
# ===========================
@login_required
def boundary_mapping(request):
    return render(request, 'boundary_mapping.html')


@login_required
def fertilizer_recommendation(request):
    crops = Crop.objects.all().order_by("name")
    stages = [stage[0] for stage in FertilizerStageMapping.STAGE_CHOICES]

    # Map fertilizers to each stage
    stage_fertilizers = {}
    for stage in stages:
        ferts = FertilizerStageMapping.objects.filter(stage_name=stage).select_related('fertilizer')
        stage_fertilizers[stage] = [
            {
                "id": f.fertilizer.id,
                "name": f.fertilizer.name,
                "n_percent": f.fertilizer.n_percent,
                "p_percent": f.fertilizer.p_percent,
                "k_percent": f.fertilizer.k_percent,
            }
            for f in ferts
        ]

    stage_fertilizers_json = json.dumps(stage_fertilizers, cls=DjangoJSONEncoder)

    context = {
    "crops": crops,
    "stages": stages,
    "stage_fertilizers_json": stage_fertilizers_json,
}
    return render(request, "fertilizer_recommendation.html", context)


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
    context = {"SOIL_REPORTS": SOIL_REPORTS}
    return render(request, "soil_taxonomy.html", context)



# ===========================
# Farm Boundary Endpoints
# ===========================
@login_required
def save_farm_boundary(request):
    """Save farm boundary from form submission"""
    if request.method == "POST":
        farm_name = request.POST.get("farm_name")
        location = request.POST.get("location")
        boundary = request.POST.get("boundary")
        area = request.POST.get("area")

        if not all([farm_name, location, boundary, area]):
            messages.error(request, "All fields are required.")
            return redirect('boundary_mapping')

        try:
            geom = GEOSGeometry(json.dumps(json.loads(boundary)["geometry"]))
            FarmBoundary.objects.create(
                owner=request.user,
                name=farm_name,
                location=location,
                boundary=geom,
                area=float(area)
            )
            messages.success(request, "Farm boundary saved successfully.")
        except Exception as e:
            messages.error(request, f"Error saving boundary: {e}")

        return redirect('boundary_mapping')
    else:
        return redirect('boundary_mapping')


@login_required
@csrf_exempt
def save_boundary(request):
    """Save farm boundary via AJAX / JSON"""
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


# ===========================
# Counties & Geometry
# ===========================
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


# ===========================
# NDVI / Time Series
# ===========================
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


# ===========================
# Soil Nutrients
# ===========================
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


# ===========================
# Soil Taxonomy Endpoints
# ===========================
@login_required
def get_county_soils_with_names(request):
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
    county_name = request.GET.get("county")
    if not county_name:
        return JsonResponse({"error": "County name not provided"}, status=400)

    try:
        kenya_counties = ee.FeatureCollection("projects/ee-collinsmwiti98/assets/KenyaCounties")
        kenya_soils = ee.FeatureCollection("projects/ee-collinsmwiti98/assets/kenyasoils_styled")
        county_fc = kenya_counties.filter(ee.Filter.eq("COUNTY", county_name))
        county_soils = kenya_soils.filterBounds(county_fc).select(
            ['DOMSOI', 'fillColor', 'fillOpacity', 'strokeColor', 'strokeWidth']
        )

        features = county_soils.getInfo()['features']

        geojson = {"type": "FeatureCollection", "features": []}
        for f in features:
            soil_code = f['properties'].get('DOMSOI')
            soil_name = soil_code_guide.get(soil_code, "Unknown Soil")
            geojson["features"].append({
                "type": "Feature",
                "geometry": f['geometry'],
                "properties": {
                    "DOMSOI": soil_code,
                    "Soil_Name": soil_name,
                    "fillColor": f['properties'].get('fillColor', '#cccccc'),
                    "fillOpacity": f['properties'].get('fillOpacity', 0.7),
                    "strokeColor": f['properties'].get('strokeColor', '#000000'),
                    "strokeWidth": f['properties'].get('strokeWidth', 1),
                }
            })

        return JsonResponse(geojson, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ===========================
# Plant Disease Prediction
# ===========================
@csrf_exempt
def predict_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    file: InMemoryUploadedFile = request.FILES.get("file")
    crop = request.POST.get("crop", "").lower()
    
    if not file:
        return JsonResponse({"error": "No file uploaded"}, status=400)
    if crop not in MODELS or MODELS[crop] is None:
        return JsonResponse({"error": f"No model available for crop '{crop}'"}, status=400)

    model = MODELS[crop]

    # Get the actual model and input size
    model_info = MODELS[crop]        # dict with 'model' and 'input_size'
    model = model_info['model']      # actual Keras model
    TARGET_SIZE = model_info['input_size']  # use the stored input size

    try:
        # Load and preprocess image
        img = image.load_img(BytesIO(file.read()), target_size=TARGET_SIZE)
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0

        # Make prediction
        preds = model.predict(img_array)
        predicted_class_idx = int(np.argmax(preds[0]))
        confidence = float(np.max(preds[0]))

        # Class labels
        CLASS_LABELS = {
            "potato": ["Potato___Early_blight", "Potato___healthy", "Potato___Late_blight"],
            "wheat": ['aphid_valid', 'black_rust_valid', 'blast_test_valid', 'brown_rust_valid',
                      'common_root_rot_valid', 'fusarium_head_blight_valid', 'healthy_valid',
                      'leaf_blight_valid', 'mildew_valid', 'mite_valid', 'septoria_valid',
                      'smut_valid', 'stem_fly_valid', 'tan_spot_valid', 'yellow_rust_valid'],
            "tomato": ['Tomato___Bacterial_spot', 'Tomato___Early_blight', 'Tomato___Late_blight',
                       'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot',
                       'Tomato___Spider_mites Two-spotted_spider_mite', 'Tomato___Target_Spot',
                       'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus',
                       'Tomato___healthy'],
            "maize": ['Cercospora_leaf_spot Gray_leaf_spot', 'Common_rust_', 'Gray_Leaf_Spot',
                      'Healthy', 'Northern_Leaf_Blight']
        }

        disease = CLASS_LABELS.get(crop, ["Unknown"])[predicted_class_idx]

        # Example stage/treatment - can be improved later
        stage = "Early"
        treatment = "Apply recommended fungicide"

        return JsonResponse({
            "prediction": disease,
            "confidence": confidence,
            "stage": stage,
            "treatment": treatment,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ===========================
# Fertilizer Recommendation API
# ===========================
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


# ===========================
# Reverse Geocoding
# ===========================
@csrf_exempt
def reverse_geocode(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    try:
        body = json.loads(request.body)
        lat = body.get("lat")
        lng = body.get("lng")
        if not all([lat, lng]):
            return JsonResponse({"error": "Missing lat/lng"}, status=400)

        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lng}"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()
        address = data.get("display_name", "")
        return JsonResponse({"address": address})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ===========================
# Soil Reports Mapping
# ===========================
# Map soil names to PDF report files


def download_soil_report(request, soil_code):
    if soil_code not in SOIL_REPORTS:
        raise Http404("No report found for this soil type")

    report_filename = SOIL_REPORTS[soil_code]
    file_path = os.path.join(settings.BASE_DIR, "static", "reports", report_filename)

    if not os.path.exists(file_path):
        raise Http404("Report file not found on server")

    return FileResponse(open(file_path, "rb"), as_attachment=True, filename=report_filename)




@login_required
def soil_summary(request, soil_name):
    """
    Render a page showing the soil report PDF and optional summary.
    """
    pdf_file = SOIL_REPORTS.get(soil_name)
    pdf_url = static(f'reports/{pdf_file}') if pdf_file else None

    # Optional: you can include textual summary from soil_summaries.py
    summary_text = soil_summaries.get(soil_name, "")

    context = {
        "soil_name": soil_name,
        "pdf_url": pdf_url,
        "summary": summary_text,
    }
    return render(request, "soil_summary.html", context)

@login_required
def crop_applications_api(request, crop_id):
    """
    Returns the number of fertilizer applications for a given crop
    """
    try:
        app_data = CropApplication.objects.get(crop__id=crop_id)
        return JsonResponse({
            "num_applications": app_data.num_applications,
            "description": app_data.description
        })
    except CropApplication.DoesNotExist:
        return JsonResponse({"error": "No application data found for this crop"}, status=404)










    


