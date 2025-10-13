console.log("soilNutrients.js loaded ✅");

// ===== Initialize Leaflet Map =====
const map = L.map('map').setView([-1.0, 37.0], 6); // Centered on Kenya

// ===== Basemaps =====
const basemaps = {
    "Esri Imagery": L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { attribution: 'Tiles &copy; Esri' }
    ),
    "Esri Labels": L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        { attribution: 'Labels &copy; Esri' }
    ),
    "OpenStreetMap": L.tileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        { attribution: '&copy; OpenStreetMap contributors' }
    )
};

basemaps["Esri Imagery"].addTo(map);
basemaps["Esri Labels"].addTo(map);


L.control.layers(basemaps).addTo(map);


// ===== DOM Elements =====
const nutrientCheckboxes = document.querySelectorAll(".form-check-input");
const resultBox = document.getElementById("result-box");
const downloadBtn = document.getElementById("download-btn");


// ===== CSRF Helper =====
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        document.cookie.split(';').forEach(c => {
            const cookie = c.trim();
            if (cookie.startsWith(name + '=')) cookieValue = decodeURIComponent(cookie.split('=')[1]);
        });
    }
    return cookieValue;
}

// ===== Map Click Event =====
let selectedPoint = null;
map.on("click", function(e) {
    selectedPoint = e.latlng;

    // Remove previous marker if exists
    if (window.lastMarker) map.removeLayer(window.lastMarker);

    // Add marker
    window.lastMarker = L.marker([selectedPoint.lat, selectedPoint.lng])
        .addTo(map)
        .bindPopup(`Selected Point: [${selectedPoint.lat.toFixed(4)}, ${selectedPoint.lng.toFixed(4)}]`)
        .openPopup();

    console.log("Point selected:", selectedPoint);

    // Fetch soil nutrient data for clicked point
    fetchSoilData(selectedPoint.lat, selectedPoint.lng);
});

// ===== Fetch Soil Data =====
function fetchSoilData(lat, lng) {
    // Get selected nutrients
    const selectedNutrients = Array.from(nutrientCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);

    if (!lat || !lng || selectedNutrients.length === 0) {
        resultBox.innerHTML = "<em>Please select at least one nutrient and click on the map.</em>";
        downloadBtn.disabled = true;
        return;
    }

    fetch("/get-soil-data/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
            lat: lat,
            lng: lng,
            nutrients: selectedNutrients
        })
    })
    .then(res => res.json())
    .then(data => {
        if (!data || Object.keys(data).length === 0) {
            resultBox.innerHTML = "<em>No data available for this location.</em>";
            downloadBtn.disabled = true;
            return;
        }

        // Display results
        const html = selectedNutrients.map(nutrient => {
            return `<strong>${nutrient}:</strong> ${data[nutrient] ?? 'N/A'}`;
        }).join("<br>");
        resultBox.innerHTML = html;

        // Enable CSV download
        downloadBtn.disabled = false;
        downloadBtn.onclick = () => {
            const csvContent = "data:text/csv;charset=utf-8," +
                "nutrient,value\n" +
                selectedNutrients.map(n => `${n},${data[n] ?? ''}`).join("\n");
            const link = document.createElement("a");
            link.href = encodeURI(csvContent);
            link.download = `soil_nutrients_${lat.toFixed(4)}_${lng.toFixed(4)}.csv`;
            link.click();
        };
    })
    .catch(err => {
        console.error("Error fetching soil data:", err);
        resultBox.innerHTML = "<em>Error fetching data. Try again.</em>";
        downloadBtn.disabled = true;
    });
}
