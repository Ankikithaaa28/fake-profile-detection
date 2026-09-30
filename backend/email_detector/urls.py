from django.urls import path
from . import views

urlpatterns = [
    path('', views.email_landing_page, name='email_page'),      
    path('detect/', views.detect_email, name='detect_email'),     
    # email/detect/
]
