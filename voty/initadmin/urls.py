from django.conf.urls import url
# from django.views import generic
from . import views

urlpatterns = [
	# globals
    url('^account/edit$', views.profile_edit, name='profile_edit'),
    url('^backoffice/mass_invite$', views.mass_invite, name='mass_invite'),
    url('^backoffice/download_csv/(?P<id>.*)$', views.download_csv, name='download_mass_invites'),
]