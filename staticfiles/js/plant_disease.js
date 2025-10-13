console.log("plant_disease.js loaded ✅");

// Grab elements
const fileInput = document.getElementById("file-input");
const previewImage = document.getElementById("preview-image");
const predictBtn = document.querySelector(".predict-btn");
const cropSelect = document.getElementById("crop-select");

// Results placeholders
const diseaseEl = document.getElementById("disease-result");
const confidenceEl = document.getElementById("confidence-result");
const stageEl = document.getElementById("stage-result");
const treatmentEl = document.getElementById("treatment-result");

// Preview uploaded image
if (fileInput) {
    fileInput.addEventListener("change", function () {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                previewImage.src = e.target.result; // replace preview
            };
            reader.readAsDataURL(file);
        }
    });
}

// Predict button logic
if (predictBtn) {
    predictBtn.addEventListener("click", async function () {
        if (!fileInput.files || fileInput.files.length === 0) {
            alert("Please upload an image first.");
            return;
        }

        const file = fileInput.files[0];
        const crop = cropSelect.value;

        // Create form data
        const formData = new FormData();
        formData.append("file", file);
        formData.append("crop", crop);

        // Show loading state
        predictBtn.disabled = true;
        predictBtn.innerText = "Predicting...";
        diseaseEl.innerText = "Detecting...";

        try {
            const resp = await fetch("/predict/", { method: "POST", body: formData });

            if (!resp.ok) throw new Error("Server error");

            const data = await resp.json();
            console.log("Prediction response:", data);

            // Fill results (depends on backend response shape)
            diseaseEl.innerText = data.prediction || "Unknown";
            confidenceEl.innerText = data.confidence
                ? (data.confidence * 100).toFixed(2) + "%"
                : "---";
            stageEl.innerText = data.stage || "N/A";
            treatmentEl.innerText = data.treatment || "N/A";
        } catch (err) {
            console.error("Prediction failed:", err);
            alert("Prediction failed. Check console for details.");
        } finally {
            predictBtn.disabled = false;
            predictBtn.innerText = "🔍 Predict";
        }
    });
}
