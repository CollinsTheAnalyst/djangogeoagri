from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
import re

# For email activation
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, "login.html", {"error": "No account found with that email."})

        user = authenticate(request, username=user_obj.username, password=password)

        if user:
            login(request, user)
            return redirect("boundary_mapping")

        else:
            return render(request, "login.html", {"error": "Invalid email or password."})

    return render(request, "login.html")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # 1. Check passwords match
        if password1 != password2:
            return render(request, "register.html", {"error": "Passwords do not match."})

        # 2. Validate username (alphanumeric + underscores)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return render(request, "register.html", {"error": "Username can only contain letters, numbers, and underscores."})

        # 3. Validate email format
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return render(request, "register.html", {"error": "Enter a valid email address."})

        # 4. Check if username already exists
        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {"error": "Username already exists."})

        # 5. Check if email already exists
        if User.objects.filter(email=email).exists():
            return render(request, "register.html", {"error": "Email already registered. Please login or use another email."})

        # 6. Create new user (inactive for activation)
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.is_active = False  # deactivate until email confirmed
        user.save()

        # 7. Send activation email
        current_site = get_current_site(request)
        mail_subject = 'Activate your account'
        message = render_to_string('activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        email_message = EmailMessage(mail_subject, message, to=[email])
        email_message.send()

        # 8. Inform user to check email
        return render(request, "registration_pending.html", {"email": email})

    return render(request, "register.html")


def activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)  # optional: log them in immediately
        return render(request, "activation_success.html")
    else:
        return render(request, "activation_invalid.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def reset_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            User.objects.get(email=email)
            # Later: send reset email with a token link
            messages.success(request, "If an account with that email exists, a reset link has been sent.")
        except User.DoesNotExist:
            messages.success(request, "If an account with that email exists, a reset link has been sent.")

        return render(request, "reset_password.html")

    return render(request, "reset_password.html")


def set_new_password_view(request):
    if request.method == "POST":
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "set_new_password.html")

        user = request.user if request.user.is_authenticated else None
        if user:
            user.set_password(password1)
            user.save()
            messages.success(request, "Password successfully updated. Please login.")
            return redirect("login")
        else:
            messages.error(request, "Invalid request. Please try again.")
            return redirect("reset_password")

    return render(request, "set_new_password.html")


def check_email_view(request):
    email = request.GET.get("email", "")
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({"exists": exists})
