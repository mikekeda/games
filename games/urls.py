"""
Games URL Configuration
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('core.urls', namespace='core')),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('admin/', admin.site.urls),
]
