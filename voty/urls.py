""" Voty URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/1.10/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r"^$", views.home, name="home")
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r"^$", Home.as_view(), name="home")
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r"^blog/", include("blog.urls"))
"""

from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import TemplateView
import notifications.urls
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings

urlpatterns = [
  url(r'^i18n/', include('django.conf.urls.i18n')),
]
urlpatterns += i18n_patterns(
  url(r"", include("voty.initadmin.urls")),
  url(r"^admin/", admin.site.urls),
  url(r"^account/", include("account.urls")),
  url(r"^avatar/", include("avatar.urls")),
  url(r"^language$", TemplateView.as_view(template_name="account/language.html")),
  url(r"^about", TemplateView.as_view(template_name="static/about.html")),
  url(r"^help", TemplateView.as_view(template_name="static/help.html")),
  url(r"^register", TemplateView.as_view(template_name="static/register.html")),
  url(r"^messages/", include(notifications.urls, namespace="notifications")),
  url(r"^messages/", include("pinax.notifications.urls")),
  url(r"", include("voty.initproc.urls")),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
