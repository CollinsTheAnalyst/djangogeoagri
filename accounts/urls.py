from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('set-new-password/', views.set_new_password_view, name='set_new_password'),
    path("check-email/", views.check_email_view, name="check_email"),
]
