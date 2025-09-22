from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
import re


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
            return redirect("home")  # redirect to dashboard/home
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

        # 6. Create new user
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()

        # 7. Redirect to login after success
        messages.success(request, "Account created successfully. Please login.")
        return redirect("login")

    return render(request, "register.html")


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
