console.log("ndvi_explorer.js loaded ✅");

// ===== DOM Elements =====
const countySelect = document.getElementById("county-select");
const metricSelect = document.getElementById("metric-select");
const startDateInput = document.getElementById("start-date");
const endDateInput = document.getElementById("end-date");
const plotBtn = document.getElementById("plot-btn");
const downloadBtn = document.getElementById("download-btn");
const ndviChartCanvas = document.getElementById("ndvi-chart");

const ctx = ndviChartCanvas.getContext("2d");
const gradient = ctx.createLinearGradient(0, 0, 0, 400);
gradient.addColorStop(0, "rgba(13,110,253,0.3)");
gradient.addColorStop(1, "rgba(13,110,253,0)");

// ===== Chart.js Setup =====
const ndviChart = new Chart(ndviChartCanvas, {
    type: "line",
    data: {
        labels: [],
        datasets: [{
            label: "NDVI/EVI",
            data: [],
            borderColor: "#0d6efd",
            backgroundColor: gradient,
            tension: 0.4,
            fill: true,
            pointRadius: 3,
            pointHoverRadius: 6,
            pointBackgroundColor: "#0d6efd"
        }]
    },

    options: {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "nearest", intersect: false },

    scales: {
        x: { 
            type: "time",
            time: { unit: "month", displayFormats: { month: "MMM yyyy" } },
            title: { display: true, text: "Date" },
            grid: {
                color: "rgba(0,0,0,0.05)",
                borderDash: [4, 4]   // subtle dashed gridlines
            }
        },
        y: { 
            title: { display: true, text: "Index Value" },
            min: 0, max: 1,
            grid: {
                color: "rgba(0,0,0,0.05)",
                borderDash: [4, 4]
            }
        }
    },

        plugins: { 
            title: { display: true, text: "NDVI/EVI Time Series" },
            tooltip: { 
                mode: "index", 
                intersect: false, 
                callbacks: {
                    label: function(context) {
                        return `${context.dataset.label}: ${context.parsed.y.toFixed(3)}`;
                    }
                }
            }, 
            legend: { display: true }
            
        }
    }
});

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

// ===== Initialize Map =====
const map = L.map('map').setView([-1.0, 37.0], 6);
const imagery = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { attribution: 'Tiles &copy; Esri' }
).addTo(map);
const labels = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
    { attribution: 'Labels &copy; Esri' }
).addTo(map);

L.control.layers({ "Esri Imagery": imagery, "Esri Labels": labels }).addTo(map);

// ===== Fetch Counties =====
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

// ===== County Geometry & Click Enable =====
let countyLayer = null;
let canSelectPoint = false;
let selectedPoint = null; // ⬅ store point until user clicks "Plot"

countySelect.addEventListener("change", () => {
    const selectedCounty = countySelect.value;
    if (!selectedCounty) return;

    fetch(`/get-county-geometry/?county=${selectedCounty}`)
        .then(res => res.json())
        .then(data => {
            if (countyLayer) map.removeLayer(countyLayer);

            countyLayer = L.geoJSON(data.geometry, {
                style: { color: "blue", weight: 2, fillOpacity: 0.1 }
            }).addTo(map);

            map.fitBounds(countyLayer.getBounds());
            canSelectPoint = true;
        })
        .catch(err => console.error("Error loading county geometry:", err));
});

// ===== Plot NDVI/EVI Time Series =====
function plotTimeSeries(lat, lng) {
    if (!lat || !lng) return;

    fetch("/point-time-series/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
            lat,
            lng,
            metric: metricSelect.value,
            start_date: startDateInput.value,
            end_date: endDateInput.value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (!Array.isArray(data) || data.length === 0) {
            ndviChart.data.labels = [];
            ndviChart.data.datasets[0].data = [];
            ndviChart.update();
            return;
        }

        const dates = data.map(d => d.date.split("T")[0]);
        const values = data.map(d => d.value);

        ndviChart.data.labels = dates;
        ndviChart.data.datasets[0].data = values;

        // Update Y axis label
        ndviChart.options.scales.y.title.text = metricSelect.value;

        // Format dates for title
        const startDate = new Date(startDateInput.value);
        const endDate = new Date(endDateInput.value);
        const startFmt = startDate.toLocaleDateString("en-US", { month: "short", year: "numeric" });
        const endFmt = endDate.toLocaleDateString("en-US", { month: "short", year: "numeric" });

        // Update chart title
        ndviChart.options.plugins.title.text = 
            `${metricSelect.value} at (${lat.toFixed(3)}, ${lng.toFixed(3)}) from ${startFmt} to ${endFmt}`;

        ndviChart.update();

        // Update dataset color based on metric
        // Update dataset color based on metric
        const metric = metricSelect.value;
        let borderColor, pointColor, gradient;

        if (metric === "NDVI") {
            borderColor = "#198754"; // green
            pointColor = "#198754";
            gradient = ctx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, "rgba(25,135,84,0.3)");
            gradient.addColorStop(1, "rgba(25,135,84,0)");
        } else {
            borderColor = "#0d6efd"; // blue
            pointColor = "#0d6efd";
            gradient = ctx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, "rgba(13,110,253,0.3)");
            gradient.addColorStop(1, "rgba(13,110,253,0)");
        }

        ndviChart.data.datasets[0].borderColor = borderColor;
        ndviChart.data.datasets[0].pointBackgroundColor = pointColor;
        ndviChart.data.datasets[0].backgroundColor = gradient;



        // Enable CSV download
        downloadBtn.disabled = false;
        downloadBtn.onclick = () => {
            const csvContent = "data:text/csv;charset=utf-8," + 
                "date,value\n" + 
                data.map(d => `${d.date},${d.value}`).join("\n");
            const link = document.createElement("a");
            link.href = encodeURI(csvContent);
            link.download = `${metricSelect.value}_timeseries.csv`;
            link.click();
        };
    })
    .catch(err => console.error("Error fetching time series:", err));
}

// ===== Map Click Event (only select point) =====
map.on("click", function(e) {
    if (!canSelectPoint) return;
    selectedPoint = e.latlng; // store clicked point
    console.log("Point selected:", selectedPoint);
});

// ===== Plot Button Event =====
plotBtn.addEventListener("click", () => {
    if (!selectedPoint) {
        alert("Please click on the map to select a location first.");
        return;
    }
    plotTimeSeries(selectedPoint.lat, selectedPoint.lng);
});
