from django.conf.urls import url
# from django.views import generic
from . import views

urlpatterns = [
	# globals
    url('^mass_invite$', views.mass_invite, name='mass_invite'),
    url('^download_csv/(?P<id>.*)$', views.download_csv, name='download_mass_invites'),
]