# blog/urls.py
from django.urls import path
from . import views

app_name = "blog"  # 👈 this line registers the namespace

urlpatterns = [
    path('', views.blog_list, name='list'),
    path('category/<slug:category_slug>/', views.blog_list, name='category'),
    path('<slug:slug>/', views.blog_detail, name='detail'),
]

