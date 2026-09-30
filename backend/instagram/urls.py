
from django.urls import path
from . import views

app_name = "instagram"  # 👈 This registers the namespace

urlpatterns = [
    path("detect/", views.detect_instagram_profile, name="detect"),
    path("", views.home, name="home"),  # optional: homepage for the app
]