console.log("soil_taxonomy.js loaded ✅");



// --- CSRF Helper ---
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
const csrftoken = getCookie('csrftoken');

function setSelectedSoil(soilCode) {
    selectedSoilCode = soilCode;
    // Enable the button if soilCode exists
    downloadBtn.disabled = !soilCode;
}


// ===== Initialize Map =====
const map = L.map('map').setView([-1.0, 37.0], 6);

// Add geocoder search bar
L.Control.geocoder({
    position: 'topright',
    defaultMarkGeocode: true,
    placeholder: "🔍 Search county or coordinates..."
})
.on('markgeocode', function(e) {
    const bbox = e.geocode.bbox;
    map.fitBounds(bbox);
})
.addTo(map);
console.log("✅ Geocoder added to map!");

// Base layers
const imagery = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { attribution: 'Tiles &copy; Esri' }
).addTo(map);

const labels = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
    { attribution: 'Labels &copy; Esri' }
).addTo(map);

L.control.layers({ "Esri Imagery": imagery, "Esri Labels": labels }).addTo(map);

// ===== Global Variables =====
let countyLayer = null;
let soilLayer = null;
const countySelect = document.getElementById("county-select");
const infoPanel = document.getElementById("soil-info");
const downloadBtn = document.getElementById('download-report-btn');
let selectedSoilCode = null;

// ===== Populate county dropdown =====
fetch("/get-counties/")
  .then(res => res.json())
  .then(data => {
      if (Array.isArray(data.counties)) {
          data.counties.forEach(county => {
              const option = document.createElement("option");
              option.value = county;
              option.textContent = county;
              countySelect.appendChild(option);
          });
      }
  })
  .catch(err => console.error("Error fetching counties:", err));

// ===== County change event =====
countySelect.addEventListener("change", () => {
    const selectedCounty = countySelect.value;
    if (!selectedCounty) return;

    fetch(`/get-county-geometry/?county=${encodeURIComponent(selectedCounty)}`)
      .then(res => res.json())
      .then(data => {
          if (countyLayer) map.removeLayer(countyLayer);

          countyLayer = L.geoJSON(data.geometry, {
              style: { color: "red", weight: 2, fillOpacity: 0.05 }
          }).addTo(map);

          map.fitBounds(countyLayer.getBounds());
          loadCountySoils(selectedCounty);
      })
      .catch(err => console.error("Error loading county geometry:", err));
});

// ===== Load County Soils =====
function loadCountySoils(countyName) {
    fetch(`/get-clipped-soils/?county=${encodeURIComponent(countyName)}`)
      .then(res => res.json())
      .then(data => {
          if (soilLayer) map.removeLayer(soilLayer);

          soilLayer = L.geoJSON(data, {
              style: feature => ({
                  color: feature.properties.strokeColor || "#000000",
                  weight: feature.properties.strokeWidth || 1,
                  fillColor: feature.properties.fillColor || "#cccccc",
                  fillOpacity: feature.properties.fillOpacity || 0.5
              }),
              onEachFeature: (feature, layer) => {
                  const soilCode = feature.properties.DOMSOI || "Unknown";

                  fetch(`/get-soil-info/?code=${soilCode}`)
                    .then(res => res.json())
                    .then(soilInfo => {
                        const soilName = soilInfo.name || "Unknown";
                        const soilDescription = soilInfo.description || "";

                        layer.bindPopup(`
                            <b>Soil Code:</b> ${soilCode}<br>
                            <b>Name:</b> ${soilName}<br>
                            <b>Description:</b> ${soilDescription}<br>
                            <i>Click again to get location...</i>
                        `);

                        layer.on("click", function () {
                            const bounds = layer.getBounds();
                            const center = bounds.getCenter();

                            fetch("/reverse-geocode/", {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                    "X-CSRFToken": csrftoken
                                },
                                body: JSON.stringify({ lat: center.lat, lng: center.lng })
                            })
                            .then(res => res.json())
                            .then(locData => {
                                const locationName = locData.address || "Unknown location";
                                const markdownContent = `
**📍 Location:** ${locationName}
**🧭 Soil Code:** ${soilCode}
**🌱 Soil Type:** ${soilName}

${soilDescription}
                                `;
                                infoPanel.innerHTML = marked.parse(markdownContent);
                                infoPanel.scrollTop = 0;

                                // ✅ Enable download button if report exists
                                setSelectedSoil(soilCode);
                                if (SOIL_REPORTS[selectedSoilCode]) {
                                    downloadBtn.disabled = false;
                                } else {
                                    downloadBtn.disabled = true;
                                }
                            })
                            .catch(err => console.error("Error reverse-geocoding:", err));
                        });
                    });
              }
          }).addTo(map);
      })
      .catch(err => console.error("Error loading soils:", err));
}

// ===== Map click to fetch soil at point =====
map.on("click", e => {
    const { lat, lng } = e.latlng;

    fetch("/get-soil-at-point/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken
        },
        body: JSON.stringify({ lat, lng })
    })
    .then(async res => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    })
    .then(soilData => {
        if (soilData.error) {
            infoPanel.innerHTML = `<p class="text-danger">${soilData.error}</p>`;
            downloadBtn.disabled = true;
            return;
        }

        fetch("/reverse-geocode/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken
            },
            body: JSON.stringify({ lat, lng })
        })
        .then(res => res.json())
        .then(locData => {
            const locationName = locData.address || "Unknown location";
;
            const markdownContent = `
**📍 Location:** ${locationName}
**🧭 Soil Code:** ${soilData.soil_code}
**🌱 Soil Type:** ${soilData.soil_name}

${soilData.summary || ""}
            `;
            infoPanel.innerHTML = marked.parse(markdownContent);
            infoPanel.scrollTop = 0;

            // ✅ Enable download button if report exists
            setSelectedSoil(soilData.soil_code);

            if (SOIL_REPORTS[selectedSoilCode]) {
                downloadBtn.disabled = false;
            } else {
                downloadBtn.disabled = true;
            }
        });
    })
    .catch(err => {
        console.error("Error fetching soil at point:", err);
        infoPanel.innerHTML = `<p class="text-danger">Error fetching soil at this point.</p>`;
        downloadBtn.disabled = true;
    });
});

// ===== Download button click =====
downloadBtn.addEventListener('click', () => {
    if (selectedSoilCode) {
        const url = `/soilreport/${selectedSoilCode}/download/`;
        window.open(url, '_blank');
    }
});





