document.addEventListener("DOMContentLoaded", () => {
    // --- DOM Elements ---
    const cropSelect = document.getElementById("crop");
    const sizeInput = document.getElementById("size");
    const unitSelect = document.getElementById("unit");
    const nutrientValuesRow = document.getElementById("nutrientValues");

    const stageRadios = document.querySelectorAll('input[name="stage"]');
    const fertilizerSelect = document.getElementById("fertilizer");
    const fertN = document.getElementById("fert-n");
    const fertP = document.getElementById("fert-p");
    const fertK = document.getElementById("fert-k");

    // --- Data ---
    let nutrientData = null;

    // ✅ The global variable injected from the template
    // (Use window.stageFertilizers instead of parsing template strings inside JS)
    const stageFertilizers = window.stageFertilizers || {};

    // --- Functions ---
    function clearTotals() {
        if (!nutrientValuesRow) return;
        nutrientValuesRow.children[0].textContent = "0";
        nutrientValuesRow.children[1].textContent = "0";
        nutrientValuesRow.children[2].textContent = "0";
    }

    function updateTotals() {
        if (!nutrientData) {
            clearTotals();
            return;
        }
        let size = parseFloat(sizeInput.value);
        if (isNaN(size) || size < 0) size = 0;
        if (unitSelect.value === "Acres") size *= 0.4047;

        const N = parseFloat(nutrientData.N) || 0;
        const P = parseFloat(nutrientData.P) || 0;
        const K = parseFloat(nutrientData.K) || 0;

        nutrientValuesRow.children[0].textContent = (N * size).toFixed(0);
        nutrientValuesRow.children[1].textContent = (P * size).toFixed(0);
        nutrientValuesRow.children[2].textContent = (K * size).toFixed(0);
    
        updateRecommendationBox();

    
    }

    function populateFertilizers(stage) {
        fertilizerSelect.innerHTML = '<option value="">-- Select Fertilizer --</option>';
        if (stageFertilizers[stage]) {
            stageFertilizers[stage].forEach(f => {
                const opt = document.createElement("option");
                opt.value = JSON.stringify(f);
                opt.textContent = f.name;
                fertilizerSelect.appendChild(opt);
            });
        }
        fertN.textContent = "0";
        fertP.textContent = "0";
        fertK.textContent = "0";
    }


const stageRadiosContainer = document.getElementById("stageRadiosContainer");

cropSelect.addEventListener("change", () => {
    const cropId = cropSelect.value;
    if (!cropId) {
        nutrientData = null;
        clearTotals();
        return;
    }

    // --- 1. Fetch crop application info ---
    fetch(`/crop-applications/${cropId}/`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            const numApps = data.num_applications;

            // ✅ Clear and rebuild the stage container dynamically
            stageRadiosContainer.innerHTML = "";

            for (let i = 1; i <= numApps; i++) {
                const stageName =
                    i === 1 ? "Planting" :
                    i === 2 ? "Top Dressing 1" :
                    i === 3 ? "Top Dressing 2" :
                    `Stage ${i}`;

                const wrapper = document.createElement("div");
                wrapper.classList.add("stage-option");

                const radio = document.createElement("input");
                radio.type = "radio";
                radio.name = "stage";
                radio.value = stageName;
                radio.id = `stage_${i}`;

                const label = document.createElement("label");
                label.htmlFor = radio.id;
                label.textContent = stageName;

                wrapper.appendChild(radio);
                wrapper.appendChild(label);
                stageRadiosContainer.appendChild(wrapper);

                // When user changes stage
                radio.addEventListener("change", () => {
                    if (radio.checked) window.populateFertilizers(radio.value);
                    updateRecommendationBox();
                });
            }

            // ✅ Automatically select the first visible stage and populate fertilizers
            const firstRadio = stageRadiosContainer.querySelector("input[name='stage']");
            if (firstRadio) {
                firstRadio.checked = true;
                window.populateFertilizers(firstRadio.value);
            } else {
                console.warn("No stage radios found or visible.");
            }

            // --- 2. Fetch nutrient requirements ---
            return fetch(`/fertilizer-api/${cropId}/`);
        })
        .then(res => res ? res.json() : null)
        .then(data => {
            if (!data) return;
            if (data.error) {
                alert(data.error);
                nutrientData = null;
                clearTotals();
                return;
            }
            nutrientData = data;
            updateTotals();
        })
        .catch(err => {
            console.error("Error fetching crop application data:", err);
            nutrientData = null;
            clearTotals();
        });
});


    sizeInput.addEventListener("input", updateTotals);
    unitSelect.addEventListener("change", updateTotals);

    stageRadios.forEach(radio => {
        radio.addEventListener("change", () => {
            if (radio.checked) populateFertilizers(radio.value);
        });
        if (radio.checked) populateFertilizers(radio.value);
    });

    fertilizerSelect.addEventListener("change", () => {
        const selected = fertilizerSelect.value;
        if (!selected) {
            fertN.textContent = "0";
            fertP.textContent = "0";
            fertK.textContent = "0";
            return;
        }
        const fData = JSON.parse(selected);
        fertN.textContent = fData.n_percent;
        fertP.textContent = fData.p_percent;
        fertK.textContent = fData.k_percent;
    });

            // --- Auto-update recommendation when inputs change ---
        fertilizerSelect.addEventListener("change", updateRecommendationBox);
        sizeInput.addEventListener("input", updateRecommendationBox);
        unitSelect.addEventListener("change", updateRecommendationBox);
        cropSelect.addEventListener("change", () => setTimeout(updateRecommendationBox, 800));
        stageRadiosContainer.addEventListener("change", updateRecommendationBox);


    // ✅ Expose this function globally for console/testing or template access
    window.populateFertilizers = populateFertilizers;

    function generateFertilizerRecommendation(numStages, nutrientReqs, fertData) {
    const areaInput = parseFloat(document.getElementById("size").value) || 1.0;
    const unit = document.getElementById("unit").value;
    const areaHa = unit === "Acres" ? areaInput * 0.4047 : areaInput;
    const haToAcre = 1 / 0.4047;

    const cropName = document.getElementById("crop").selectedOptions[0]?.text || "Crop";
    const fertName = fertData.name;
    const selectedStage = document.querySelector('input[name="stage"]:checked')?.value;

    // --- Convert to oxide forms ---
    const N_req = nutrientReqs.N;            // elemental N stays same
    const P_req = nutrientReqs.P * 2.29;     // convert to P₂O₅
    const K_req = nutrientReqs.K * 1.2;      // convert to K₂O

    const nPct = fertData.n_percent / 100;
    const pPct = fertData.p_percent / 100;
    const kPct = fertData.k_percent / 100;

    // --- Total nutrient needs (kg nutrient/ha × area in ha) ---
    const totalN = N_req * areaHa;
    const totalP = P_req * areaHa;
    const totalK = K_req * areaHa;

    let recText = "";

    // ==================== TWO-STAGE CROPS ====================
    if (numStages === 2) {
        // 🌱 Apply 100% of P at planting
        const fertForP = pPct > 0 ? totalP / pPct : 0;
        const fertPlanting = fertForP; // 100% P₂O₅ source
        const N_from_planting = fertPlanting * nPct;
        const N_remaining = Math.max(totalN - N_from_planting, 0);
        const fertTopdress = nPct > 0 ? N_remaining / nPct : 0;

        if (selectedStage === "Planting") {
            recText = `<b>${cropName}</b><br>
            Apply <b>${(fertPlanting * haToAcre).toFixed(1)} kg/acre</b> of <b>${fertName}</b>.`;
        } else if (selectedStage === "Top Dressing 1") {
            recText = `<b>${cropName}</b><br>
            Apply <b>${(fertTopdress * haToAcre).toFixed(1)} kg/acre</b> of <b>${fertName}</b>.`;
        }
    }

    // ==================== THREE-STAGE CROPS ====================
    if (numStages === 3) {
        // 🌱 Apply 100% P₂O₅ at planting
        const fertForP = pPct > 0 ? totalP / pPct : 0;
        const fertPlanting = fertForP;
        const N_from_planting = fertPlanting * nPct;

        const N_remaining = Math.max(totalN - N_from_planting, 0);
        const N_each_top = N_remaining / 2;
        const fertTopdressN = nPct > 0 ? N_each_top / nPct : 0;

        if (selectedStage === "Planting") {
            recText = `<b>${cropName}</b><br>
            Apply <b>${(fertPlanting * haToAcre).toFixed(1)} kg/acre</b> of <b>${fertName}</b>.`;
        } else if (selectedStage === "Top Dressing 1") {
            recText = `<b>${cropName}</b><br>
            Apply <b>${(fertTopdressN * haToAcre).toFixed(1)} kg/acre</b> of <b>${fertName}</b>.`;
        } else if (selectedStage === "Top Dressing 2") {
            recText = `<b>${cropName}</b><br>
            Apply <b>${(fertTopdressN * haToAcre).toFixed(1)} kg/acre</b> of <b>${fertName}</b>.`;
        }
    }

    return recText || "Select a stage to see the recommendation.";
}


function updateRecommendationBox() {
    const recEl = document.getElementById("recommendation");
    if (!recEl) return;

    const selectedFert = fertilizerSelect.value;
    if (!nutrientData || !selectedFert) {
        recEl.innerHTML = "Select crop, farm size, and fertilizer to see recommendations.";
        return;
    }

    const fertData = JSON.parse(selectedFert);

    // Count number of stages dynamically
    const numStages = document.querySelectorAll('input[name="stage"]').length;

    const recHTML = generateFertilizerRecommendation(numStages, nutrientData, fertData);
    recEl.innerHTML = recHTML;
}



    // --- Init ---
    clearTotals();
    console.log("Stage fertilizers:", stageFertilizers);
});
