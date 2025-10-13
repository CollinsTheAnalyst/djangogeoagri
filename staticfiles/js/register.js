document.addEventListener("DOMContentLoaded", function () {
    // Inputs
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const password1 = document.getElementById('password1');
    const password2 = document.getElementById('password2');

    // Feedback placeholders
    const usernameFeedback = document.getElementById('usernameFeedback');
    const emailFeedback = document.getElementById('emailFeedback');

    // Password toggle
    const togglePassword1Text = document.getElementById('togglePassword1Text');
    const togglePassword2Text = document.getElementById('togglePassword2Text');

    togglePassword1Text.addEventListener('click', () => {
        const type = password1.type === 'password' ? 'text' : 'password';
        password1.type = type;
        togglePassword1Text.textContent = type === 'password' ? 'Show' : 'Hide';
    });

    togglePassword2Text.addEventListener('click', () => {
        const type = password2.type === 'password' ? 'text' : 'password';
        password2.type = type;
        togglePassword2Text.textContent = type === 'password' ? 'Show' : 'Hide';
    });

    // Live username validation
    usernameInput.addEventListener('input', () => {
        const username = usernameInput.value.trim();
        const usernameRegex = /^[a-zA-Z0-9_]+$/;
        if (username.length === 0) {
            usernameFeedback.textContent = '';
        } else if (usernameRegex.test(username)) {
            usernameFeedback.textContent = '✅';
            usernameFeedback.style.color = 'green';
        } else {
            usernameFeedback.textContent = '❌ Only letters, numbers, underscores allowed.';
            usernameFeedback.style.color = 'red';
        }
    });

    // Live email validation
    emailInput.addEventListener('input', () => {
        const email = emailInput.value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/;
        if (email.length === 0) {
            emailFeedback.textContent = '';
        } else if (emailRegex.test(email)) {
            emailFeedback.textContent = '✅';
            emailFeedback.style.color = 'green';
        } else {
            emailFeedback.textContent = '❌ Invalid email format.';
            emailFeedback.style.color = 'red';
        }
    });
});
