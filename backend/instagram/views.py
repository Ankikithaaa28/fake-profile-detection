from django.shortcuts import render

from .detection import detect_profile


def home(request):
    """Instagram landing page: the username form."""
    return render(request, "instagram/home.html")


def detect_instagram_profile(request):
    """Thin wrapper so the URL route points at a view in views.py."""
    return detect_profile(request)
