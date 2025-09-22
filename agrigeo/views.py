from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Home / Dashboard page
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
