"""
Games URL Configuration
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.utils.translation import ugettext_lazy as _

urlpatterns = [
    path("", include("core.urls", namespace="core")),
    path("oauth/", include("social_django.urls", namespace="social")),
    path("admin/", admin.site.urls),
]

admin.site.site_header = _("Games administration")

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
