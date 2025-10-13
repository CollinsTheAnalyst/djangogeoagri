console.log("boundary_mapping.js loaded ✅");

document.addEventListener("DOMContentLoaded", function() {

    // --- DOM Elements ---
    const farmNameInput = document.getElementById('farm-name');
    const areaInfo = document.getElementById('area-info');
    const locationInput = document.getElementById('location-search');
    const mapElement = document.getElementById('map');

    if (!mapElement) {
        console.error("Map container not found!");
        return;
    }

    // --- CSRF helper ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // --- Initialize Map ---
    const map = L.map('map').setView([-1.0, 37.0], 12);

    // Hybrid tiles: Imagery + Labels
    const imagery = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { attribution: 'Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics' }
    );

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
        draw: { polygon: true, rectangle: true, polyline: false, circle: false, marker: false },
        edit: { featureGroup: drawnItems }
    });
    map.addControl(drawControl);

    // Geocoder control
    L.Control.geocoder({ defaultMarkGeocode: true }).addTo(map);

    // --- Location Search Autocomplete ---
    if (locationInput) {
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.style.position = 'absolute';
        suggestionsContainer.style.background = '#fff';
        suggestionsContainer.style.border = '1px solid #ccc';
        suggestionsContainer.style.zIndex = 1000;
        locationInput.parentNode.appendChild(suggestionsContainer);

        locationInput.addEventListener('input', function() {
            const query = locationInput.value.trim();
            suggestionsContainer.innerHTML = '';
            if (!query) return;

            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${query}`)
            .then(res => res.json())
            .then(data => {
                data.slice(0,5).forEach(d => {
                    const div = document.createElement('div');
                    div.style.padding = '4px';
                    div.style.cursor = 'pointer';
                    div.textContent = d.display_name;
                    div.addEventListener('click', () => {
                        locationInput.value = d.display_name;
                        map.setView([d.lat, d.lon], 16);
                        suggestionsContainer.innerHTML = '';

                        if (window.searchMarker) map.removeLayer(window.searchMarker);
                        window.searchMarker = L.marker([d.lat, d.lon]).addTo(map)
                            .bindPopup(d.display_name)
                            .openPopup();
                    });
                    suggestionsContainer.appendChild(div);
                });
            })
            .catch(err => console.error(err));
        });
    } else {
        console.warn("Location input not found – search disabled.");
    }

    // --- Handle Draw Created Event ---
    map.on(L.Draw.Event.CREATED, function(event) {
        const layer = event.layer;
        drawnItems.clearLayers();
        drawnItems.addLayer(layer);

        let latlngs = layer.getLatLngs();
        if (Array.isArray(latlngs[0])) latlngs = latlngs[0];

        const area_m2 = L.GeometryUtil.geodesicArea(latlngs);
        const area_ha = area_m2 / 10000;
        const area_acres = area_m2 / 4046.86;

        const farmName = farmNameInput ? farmNameInput.value.trim() || "Unnamed Farm" : "Unnamed Farm";

        if (areaInfo) {
            areaInfo.innerHTML = `<b>${farmName} Farm </b> : ${area_ha.toFixed(2)} ha (${area_acres.toFixed(2)} acres)`;
        }

        layer.bindPopup(`<b>${farmName} Farm </b> <br>${area_ha.toFixed(2)} ha (${area_acres.toFixed(2)} acres)`).openPopup();

        // Send GeoJSON to backend
        fetch("/save-boundary/", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({ 
                geojson: layer.toGeoJSON(), 
                name: farmName
            })
        })
        .then(res => res.json())
        .then(data => console.log("Saved boundary:", data))
        .catch(err => console.error(err));
    });

});
