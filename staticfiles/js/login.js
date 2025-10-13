document.addEventListener("DOMContentLoaded", function () {
    const emailInput = document.querySelector("input[name='email']");
    const emailError = document.getElementById("emailError");
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    function validateEmailFormat() {
        const email = emailInput.value.trim();
        if (email.length === 0) {
            emailError.textContent = "";
            return false;
        }
        if (!emailRegex.test(email)) {
            emailError.textContent = "Enter a valid email address.";
            return false;
        }
        emailError.textContent = "✅";
        return true;
    }

    function checkEmailExists() {
        const email = emailInput.value.trim();
        if (!validateEmailFormat()) return;

        fetch(`/check-email/?email=${encodeURIComponent(email)}`)
            .then(response => response.json())
            .then(data => {
                if (!data.exists) {
                    emailError.textContent = "No account found with this email.";
                } else {
                    emailError.textContent = "✅";
                }
            })
            .catch(err => console.error("Error checking email:", err));
    }

    // Email validation
    emailInput.addEventListener("input", validateEmailFormat);
    emailInput.addEventListener("blur", checkEmailExists);

    // Password toggle
    const password = document.getElementById("password");
    const togglePasswordText = document.getElementById("togglePasswordText");

    togglePasswordText.addEventListener("click", () => {
        const type = password.type === "password" ? "text" : "password";
        password.type = type;
        togglePasswordText.textContent = type === "password" ? "Show" : "Hide";
    });
});
