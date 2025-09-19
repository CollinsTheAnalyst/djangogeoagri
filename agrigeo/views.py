from django.shortcuts import render

# Home / Dashboard page
def home(request):
    return render(request, 'home.html')

def boundary_mapping(request):
    return render(request, 'boundary_mapping.html')

def fertilizer_recommendation(request):
    return render(request, 'fertilizer_recommendation.html')

def ndvi_explorer(request):
    return render(request, 'ndvi_explorer.html')

def plant_disease(request):
    return render(request, 'plant_disease.html')

def soil_nutrients(request):
    return render(request, 'soil_nutrients.html')

def soil_taxonomic_groups(request):
    return render(request, 'soil_taxonomy.html')

