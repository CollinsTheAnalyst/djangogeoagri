# agrigeo/views.py

import json
import os
import pandas as pd
import requests
import io  # Added for image handling
from io import BytesIO

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.templatetags.static import static
from django.conf import settings
from django.core.mail import send_mail 
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.gis.geos import GEOSGeometry

# ===========================
# AI & Image Processing Imports
# ===========================
import google.generativeai as genai
from PIL import Image

import ee

from .models import FarmBoundary, Crop, FertilizerStageMapping
from .soil_summaries import soil_summaries
from .legend import soil_code_guide

from django.http import FileResponse, Http404
from .models import CropApplication, Crop


# ===========================
# Initialize Gemini AI
# ===========================
# Check if key exists to prevent crash
if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    print("⚠️ GEMINI_API_KEY not found in settings. AI features will not work.")


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
    "Re": "Eutric Regosols.pdf",
    "G": "GLEYSOLS.pdf",
    "I": "Lithosols.pdf",
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


# =======================================================
# Dynamic/Generic Analysis Views (Hybrid - farm_id is OPTIONAL)
# =======================================================
@login_required
def ndvi_explorer(request, **kwargs):
    """
    Renders the NDVI explorer page. 
    Handles both /ndvi-explorer/ (generic) and /farm-details/<int:farm_id>/ndvi/ (dynamic).
    """
    farm_id = kwargs.get('farm_id')
    context = {}
    
    if farm_id is None:
        # 1. Generic View Logic (Initial Page Load/Selection)
        user_farms = FarmBoundary.objects.filter(owner=request.user).order_by('name')
        context.update({
            'page_title': 'NDVI Explorer - Select a Farm',
            'farms': user_farms,
            'is_selection_mode': True, # Flag for JavaScript/Template to know it's selection mode
        })
    else:
        # 2. Dynamic View Logic (Farm Selected)
        try:
            # Fetch the FarmBoundary object, ensuring it belongs to the logged-in user
            farm_boundary = FarmBoundary.objects.get(id=farm_id, owner=request.user)
            context.update({
                'page_title': f'NDVI Explorer - {farm_boundary.name}',
                'farm_id': farm_id,
                'farm_name': farm_boundary.name,
                # Pass the geometry as a GeoJSON string for use in JavaScript
                'farm_geometry': farm_boundary.boundary.json, 
                'is_selection_mode': False,
            })
        except FarmBoundary.DoesNotExist:
            messages.error(request, f"Farm with ID {farm_id} not found or you do not have permission.")
            return redirect('ndvi_explorer') # Redirect back to the selection mode

    return render(request, 'ndvi_explorer.html', context)


@login_required
def soil_nutrients(request, **kwargs):
    """
    Renders the soil nutrients page. 
    Handles both /soil-nutrients/ (generic) and /farm-details/<int:farm_id>/soil-nutrients/ (dynamic).
    """
    farm_id = kwargs.get('farm_id')
    context = {}

    if farm_id is None:
        # 1. Generic View Logic (Initial Page Load/Selection)
        user_farms = FarmBoundary.objects.filter(owner=request.user).order_by('name')
        context.update({
            'page_title': 'Soil Nutrients - Global View',
            'farms': user_farms,
            'is_selection_mode': True,
        })
    else:
        # 2. Dynamic View Logic (Farm Selected)
        try:
            farm_boundary = FarmBoundary.objects.get(id=farm_id, owner=request.user)
            context.update({
                'page_title': f'Soil Nutrients - {farm_boundary.name}',
                'farm_id': farm_id,
                'farm_name': farm_boundary.name,
                'farm_geometry': farm_boundary.boundary.json, 
                'is_selection_mode': False,
            })
        except FarmBoundary.DoesNotExist:
            messages.error(request, f"Farm with ID {farm_id} not found or you do not have permission.")
            return redirect('soil_nutrients') # Redirect back to the selection mode
            
    return render(request, 'soil_nutrients.html', context)


@login_required
def soil_taxonomic_groups(request, **kwargs):
    """
    Renders the soil taxonomy page.
    Handles both /soil-taxonomy/ (generic) and /farm-details/<int:farm_id>/soil-taxonomy/ (dynamic).
    """
    farm_id = kwargs.get('farm_id')
    context = {"SOIL_REPORTS": SOIL_REPORTS} # Always include global reports data

    if farm_id is None:
        # 1. Generic View Logic (Initial Page Load/Selection)
        user_farms = FarmBoundary.objects.filter(owner=request.user).order_by('name')
        context.update({
            'page_title': 'Soil Taxonomy - Global View',
            'farms': user_farms,
            'is_selection_mode': True,
        })
    else:
        # 2. Dynamic View Logic (Farm Selected)
        try:
            farm_boundary = FarmBoundary.objects.get(id=farm_id, owner=request.user)
            context.update({
                'page_title': f'Soil Taxonomy - {farm_boundary.name}',
                'farm_id': farm_id,
                'farm_name': farm_boundary.name,
                'farm_geometry': farm_boundary.boundary.json, 
                'is_selection_mode': False,
            })
        except FarmBoundary.DoesNotExist:
            messages.error(request, f"Farm with ID {farm_id} not found or you do not have permission.")
            return redirect('soil_taxonomic_groups') # Redirect back to the selection mode
            
    return render(request, "soil_taxonomy.html", context)


@login_required
def plant_disease(request):
    return render(request, 'plant_disease.html')


# ===========================
# Farm Boundary Endpoints
# ===========================
@login_required
@csrf_exempt
def save_farm_boundary(request):
    """
    Save farm boundary from AJAX request.
    Returns JSON response with client-side fields for modal display.
    """
    if request.method != "POST":
        return JsonResponse({"status": "failed", "error": "POST request required."}, status=405)

    try:
        # 1. Capture data from POST request
        farm_name = request.POST.get("name") 
        boundary_geojson_str = request.POST.get("geometry")
        
        # Capture client-side fields for modal display
        location_val = request.POST.get("location") 
        area_val = request.POST.get("area") 
        county_val = request.POST.get("county") 
        
        if not all([farm_name, boundary_geojson_str]):
            return JsonResponse({"status": "failed", "error": "Missing required data (Farm Name or Boundary Geometry)."}, status=400)

        # 2. Parse GeoJSON
        geom = GEOSGeometry(boundary_geojson_str)
        
        # 3. Save to database
        farm_boundary = FarmBoundary.objects.create(
            owner=request.user,
            name=farm_name,
            boundary=geom,
            area=float(area_val) if area_val else 0.0
        )
        
        # 4. Success: Return JSON response
        return JsonResponse({
            "status": "success", 
            "message": "Farm boundary saved successfully.",
            "farm_id": farm_boundary.id,
            "area": area_val,
            "county": county_val,       
            "location_name": location_val 
        })
        
    except Exception as e:
        print(f"Error saving boundary: {e}")
        return JsonResponse({"status": "failed", "error": f"Internal server error: {e}"}, status=500)
        
@login_required
@csrf_exempt
def save_boundary(request):
    """Save farm boundary via AJAX / JSON - Kept for compatibility."""
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
    """API to fetch list of county names for dropdown."""
    try:
        kenya_counties = ee.FeatureCollection("projects/ee-collinsmwiti98/assets/KenyaCounties")
        county_names = kenya_counties.aggregate_array("COUNTY").distinct().getInfo()
        return JsonResponse({"counties": county_names})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def get_county_geometry(request):
    """API to fetch GeoJSON geometry for a selected county."""
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
# AI Plant Disease Prediction (Gemini Powered)
# ===========================
@csrf_exempt
def predict_view(request):
    """
    Analyzes a plant leaf image using Google Gemini to detect disease,
    stage, and recommend treatment using a highly specific prompt.
    Includes DEBUG logic to force API key loading and show errors in the UI.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)

    # 1. Get the Data
    uploaded_file = request.FILES.get("file")
    crop_name = request.POST.get("crop", "plant")

    if not uploaded_file:
        return JsonResponse({"error": "No image file uploaded"}, status=400)

    try:
        # --- DEBUG START: Force Configuration Here ---
        # This ensures we grab the key right now, even if settings loaded early.
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        
        if not api_key:
            # This specific error will now show up in your browser's "Treatment" box
            raise ValueError("CRITICAL: GEMINI_API_KEY is missing from settings.py!")
            
        # Re-configure explicitly to be safe
        genai.configure(api_key=api_key)
        # --- DEBUG END ---

        # 2. Process Image for Gemini
        image_bytes = uploaded_file.read()
        img = Image.open(io.BytesIO(image_bytes))

        # 3. YOUR NEW ADVANCED PROMPT
        prompt = f"""
        You are an expert agronomist with deep experience diagnosing foliar problems on crops. You will be given a single image of a {crop_name} leaf (front and/or back) and must produce a single JSON object as your output. Do not add any text before or after the JSON — output only valid JSON with exactly the keys and value types described below.

        Procedure (how to analyze the image):
        1. Confirm the subject is a plant leaf. If not clearly a plant/leaf, return "Unknown/Not a Plant".
        2. Visually inspect color changes, spots, lesions, margins, patterns (random, concentric, angular), distribution across the lamina and veins, necrosis vs. chlorosis, pustules, powdery growth, insect bodies or eggs, frass, webs, and signs on the leaf underside if visible.
        3. Assess whether symptoms are biotic (fungus, bacteria, virus, insect) or abiotic (nutrient deficiency, sunburn, chemical damage, water stress). Prefer the single most likely primary diagnosis based on visible signs.
        4. Estimate stage of attack using these categories: "Early Stage" (few localized symptoms, low coverage), "Middle Stage" (moderate spread, some tissue damage), "Late/Severe Stage" (widespread lesions, extensive necrosis or defoliation).
        5. Formulate a concise, actionable recommendation (maximum 2 sentences). Include cultural controls and/or specific chemical class or active ingredient examples only if appropriate for the likely cause. Avoid long protocols; one targeted action and one follow-up suggestion is enough.
        6. Provide a numeric confidence from 0.0 to 1.0 reflecting how certain you are based solely on the image (0.0 = no confidence, 1.0 = certain).

        Output requirements (strict):
        - Return ONLY valid JSON.
        - The JSON object must contain exactly these keys in any order:
          {{
            "prediction": string,
            "confidence": number,
            "stage": string,
            "treatment": string
          }}
        - "prediction": the disease/pest common name or "Healthy" or "Unknown/Not a Plant".
        - "confidence": a floating-point number between 0.0 and 1.0 (e.g., 0.85).
        - "stage": one of "Early Stage", "Middle Stage", or "Late/Severe Stage" (or "N/A" if prediction is "Healthy" or "Unknown/Not a Plant").
        - "treatment": a brief actionable recommendation (max two sentences). If "Healthy" or "Unknown/Not a Plant" provide an appropriate short message (e.g., "No treatment needed." or "Image unclear; retake with clearer focus and include crop context.").

        Additional instructions:
        - If multiple potential causes are visible, choose the primary cause you judge most likely and base the treatment on that.
        - Do not include explanations, confidence rationale, step-by-step reasoning, or any extra fields.
        - Use plain English disease/pest names (e.g., "Late blight", "Powdery mildew", "Aphid infestation", "Nutrient deficiency (Nitrate)") when possible.
        - Keep the treatment field concise and actionable, naming a chemical class or example active ingredient only when necessary (e.g., "Apply a systemic triazole fungicide or copper spray; remove and destroy infected leaves.").
        - If the image is ambiguous or too low-quality to diagnose, set "prediction" to "Unknown/Not a Plant" and provide a short guidance sentence in "treatment" about retaking the photo (max two sentences).

        Example valid outputs:
        {{"prediction":"Healthy","confidence":0.98,"stage":"N/A","treatment":"No treatment needed; continue routine monitoring and balanced nutrition."}}
        {{"prediction":"Powdery mildew","confidence":0.75,"stage":"Early Stage","treatment":"Apply a contact fungicide (sulfur or potassium bicarbonate) and improve air circulation by pruning; monitor weekly for spread."}}

        Now analyze the provided image of a {crop_name} leaf and output the required JSON object only.
        """

        # 4. Call Gemini Model
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([prompt, img])

        # 5. Clean and Parse Response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if Gemini adds them
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()

        data = json.loads(response_text)

        # 6. Return to Frontend
        return JsonResponse(data)

    except Exception as e:
        # --- DEBUG ERROR HANDLING ---
        # This grabs the actual error (e.g. "403 Forbidden" or "Key missing")
        error_message = str(e)
        print(f"❌ DEBUG ERROR: {error_message}") # Prints to your terminal
        
        # Returns the error to the web page so you can read it without checking the terminal
        return JsonResponse({
            "prediction": "Analysis Failed",
            "confidence": 0,
            "stage": "See Error Below",
            "treatment": f"ERROR: {error_message}" 
        }, status=200)

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
    

def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Optional: send email - requires send_mail import and configuration
        # send_mail(
        #     f'Contact Form Message from {name}',
        #     message,
        #     settings.DEFAULT_FROM_EMAIL,
        #     [settings.DEFAULT_FROM_EMAIL],
        #     fail_silently=True,
        # )
        
        return render(request, 'contact.html', {'success': True})
    
    return render(request, 'contact.html')