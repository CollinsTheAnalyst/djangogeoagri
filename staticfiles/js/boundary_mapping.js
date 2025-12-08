console.log("boundary_mapping.js loaded ✅");

document.addEventListener("DOMContentLoaded", function() {

    // --- DOM Elements ---
    const farmNameInput = document.getElementById('farm_name');
    const areaInfo = document.getElementById('calculatedArea');
    const areaDisplay = document.getElementById('areaDisplay'); 
    const locationInput = document.getElementById('location'); 
    const countySelect = document.getElementById('county-select');
    const mapElement = document.getElementById('map');

    // Global variable to track the county boundary layer
    let countyLayer = null;

    if (!mapElement) {
        console.error("Map container not found!");
        return;
    }

    // --- Initialize Map ---
    const map = L.map('map').setView([-1.0, 37.0], 6); // Default Kenya View

    // Imagery
    const imagery = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { attribution: 'Tiles &copy; Esri' }
    );

    // Labels
    const labels = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        { attribution: 'Labels &copy; Esri' }
    );

    imagery.addTo(map);
    labels.addTo(map);

    // FeatureGroup for drawn items
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    // Draw control
    const drawControl = new L.Control.Draw({
        draw: { 
            polygon: {
                allowIntersection: false,
                showArea: true,
                shapeOptions: { color: '#60c844' }
            }, 
            rectangle: true, 
            polyline: false, 
            circle: false, 
            marker: false,
            circlemarker: false
        },
        edit: { featureGroup: drawnItems }
    });
    map.addControl(drawControl);

    // --- 1. DYNAMIC COUNTY FETCHING (Matches NDVI Explorer) ---
    
    // Fetch list of counties from backend
    fetch("/get-counties/")
        .then(res => res.json())
        .then(data => {
            if (Array.isArray(data.counties)) {
                // Sort alphabetically for better UX
                data.counties.sort((a, b) => a.localeCompare(b));
                
                data.counties.forEach(county => {
                    const option = document.createElement("option");
                    option.value = county;
                    option.textContent = county;
                    countySelect.appendChild(option);
                });
            }
        })
        .catch(err => console.error("Error fetching counties:", err));

    // Handle County Selection & Zoom
    if (countySelect) {
        countySelect.addEventListener("change", () => {
            const selectedCounty = countySelect.value;
            if (!selectedCounty) return;

            // Fetch geometry from backend
            fetch(`/get-county-geometry/?county=${encodeURIComponent(selectedCounty)}`)
                .then(res => res.json())
                .then(data => {
                    // Remove previous county layer if it exists
                    if (countyLayer) map.removeLayer(countyLayer);

                    // Add new county boundary (visual reference only)
                    if (data.geometry) {
                        countyLayer = L.geoJSON(data.geometry, {
                            style: { 
                                color: "#3388ff", 
                                weight: 2, 
                                fillOpacity: 0.05 // Very transparent fill
                            }
                        }).addTo(map);

                        // Zoom map to the county bounds
                        map.fitBounds(countyLayer.getBounds());
                    }
                })
                .catch(err => console.error("Error loading county geometry:", err));
        });
    }

    // --- 2. LOCATION SEARCH AUTOCOMPLETE (Kept from previous version) ---
    if (locationInput) {
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = "list-group"; 
        suggestionsContainer.style.position = 'absolute';
        suggestionsContainer.style.zIndex = 1000;
        suggestionsContainer.style.width = "100%";
        locationInput.parentNode.appendChild(suggestionsContainer);
        locationInput.parentNode.style.position = 'relative';

        locationInput.addEventListener('input', function() {
            const query = locationInput.value.trim();
            suggestionsContainer.innerHTML = '';
            
            if (query.length < 3) return; 

            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${query}&countrycodes=ke`) 
            .then(res => res.json())
            .then(data => {
                suggestionsContainer.innerHTML = ''; 
                
                data.slice(0,5).forEach(d => {
                    const item = document.createElement('a');
                    item.className = "list-group-item list-group-item-action";
                    item.style.cursor = 'pointer';
                    item.innerHTML = `<small>${d.display_name}</small>`;
                    
                    item.addEventListener('click', () => {
                        locationInput.value = d.display_name;
                        const lat = parseFloat(d.lat);
                        const lon = parseFloat(d.lon);
                        map.setView([lat, lon], 14); 
                        suggestionsContainer.innerHTML = '';

                        if (window.searchMarker) map.removeLayer(window.searchMarker);
                        window.searchMarker = L.marker([lat, lon]).addTo(map)
                            .bindPopup(d.display_name)
                            .openPopup();
                    });
                    suggestionsContainer.appendChild(item);
                });
            })
            .catch(err => console.error("Geocoding error:", err));
        });
        
        document.addEventListener('click', function(e) {
            if (e.target !== locationInput) {
                suggestionsContainer.innerHTML = '';
            }
        });
    } else {
        console.warn("Location input not found – search disabled.");
    }

    // --- 3. HANDLE DRAWING & CALCULATION ---
    map.on(L.Draw.Event.CREATED, function(event) {
        const layer = event.layer;
        
        drawnItems.clearLayers(); // Only allow one boundary
        drawnItems.addLayer(layer);

        // Calculate Area
        const latlngs = layer.getLatLngs()[0];
        const area_m2 = L.GeometryUtil.geodesicArea(latlngs);
        const area_ha = area_m2 / 10000;
        const area_acres = area_m2 / 4046.86;

        const name = farmNameInput ? farmNameInput.value : "My Farm";

        // Update UI
        if (areaInfo && areaDisplay) {
            areaInfo.innerText = area_acres.toFixed(2);
            areaDisplay.classList.remove('d-none');
            
            const saveBtn = document.getElementById('saveBoundaryButton');
            if(saveBtn) saveBtn.classList.remove('d-none');
        }

        layer.bindPopup(`<b>${name}</b><br>Area: ${area_acres.toFixed(2)} acres`).openPopup();

        // Populate hidden inputs
        const geoInput = document.getElementById('geometry_output');
        const areaInput = document.getElementById('area_output');
        
        if(geoInput) geoInput.value = JSON.stringify(layer.toGeoJSON());
        if(areaInput) areaInput.value = area_ha.toFixed(4); 
    });
    
    // Draw Button Helper
    const startDrawBtn = document.getElementById('startDrawing');
    if (startDrawBtn) {
        startDrawBtn.addEventListener('click', function() {
            new L.Draw.Polygon(map, drawControl.options.draw.polygon).enable();
        });
    }
});