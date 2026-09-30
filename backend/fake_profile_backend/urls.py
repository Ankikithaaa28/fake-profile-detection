"""
URL configuration for fake_profile_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]"""


from django.contrib import admin
from django.urls import path, include
from fake_profile_backend import views  # import frontend views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Frontend pages
    path('', views.index, name='home'),
    path('email_page/', views.email_landing_page, name='email_page'),
    
    path('instagram_page/', views.instagram_page, name='instagram_page'),
    path('x_page/', views.x_page, name='x_page'),


    # Backend detection apps
    path('email/', include('email_detector.urls')),        # email app
    path('instagram/', include('instagram.urls')), # Instagram app
    path('x/', include('x.urls')),                 # X app
]