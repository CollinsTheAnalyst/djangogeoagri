document.addEventListener('DOMContentLoaded', function() {
    console.log("plant_disease.js loaded ✅");

    // 1. Grab Elements
    const fileInput = document.getElementById("file-input");
    const previewImage = document.getElementById("preview-image");
    const predictBtn = document.getElementById("predict-btn") || document.querySelector(".predict-btn"); 
    const cropSelect = document.getElementById("crop-select");

    // 2. Result Placeholders
    const diseaseEl = document.getElementById("disease-result");
    const confidenceEl = document.getElementById("confidence-result");
    const stageEl = document.getElementById("stage-result");
    const treatmentEl = document.getElementById("treatment-result");
    
    const causesEl = document.getElementById("causes-result");
    const chemicalEl = document.getElementById("chemical-result");

    // 3. Image Preview Logic
    if (fileInput) {
        fileInput.addEventListener("change", function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    previewImage.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // 4. Predict Button Logic
    if (predictBtn) {
        predictBtn.addEventListener("click", async function () {
            if (!fileInput.files || fileInput.files.length === 0) {
                alert("Please select an image first.");
                return;
            }

            const file = fileInput.files[0];
            const crop = cropSelect.value;

            // Prepare Form Data
            const formData = new FormData();
            formData.append("file", file);
            formData.append("crop", crop);

            // ============================================================
            // 🟢 START ANIMATION (The part you mentioned)
            // ============================================================
            predictBtn.disabled = true;
            predictBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
            
            // Set temporary status messages
            diseaseEl.innerText = "Consulting AI...";
            if(causesEl) causesEl.innerText = "Analyzing symptoms...";
            if(chemicalEl) chemicalEl.innerText = "Checking PCPB Database...";

            try {
                // Send Request
                const resp = await fetch("/predict/", { method: "POST", body: formData });

                if (!resp.ok) {
                    throw new Error(`Server Error: ${resp.status}`);
                }

                const data = await resp.json();
                console.log("AI Response:", data);

                // Update UI with Data
                diseaseEl.innerText = data.prediction || "Unknown";
                confidenceEl.innerText = data.confidence
                    ? (data.confidence * 100).toFixed(1) + "%"
                    : "---";
                stageEl.innerText = data.stage || "N/A";
                treatmentEl.innerText = data.treatment || "No cultural advice found.";

                if (causesEl) causesEl.innerText = data.causes || "Information not available.";
                if (chemicalEl) chemicalEl.innerText = data.chemical_advice || "No chemical advice found.";

            } catch (err) {
                console.error("Prediction failed:", err);
                diseaseEl.innerText = "Analysis Failed";
                treatmentEl.innerText = "Connection failed. Please check your internet.";
                if(chemicalEl) chemicalEl.innerText = "---";
            } finally {
                // ============================================================
                // 🔴 STOP ANIMATION (This runs when it's done)
                // ============================================================
                predictBtn.disabled = false;
                predictBtn.innerHTML = '🔍 Diagnose Now'; 
            }
        });
    }
});