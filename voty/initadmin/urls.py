from django.conf.urls import url
# from django.views import generic
from . import views

urlpatterns = [
	# globals
    url('^debug$', views.debug, name='debug'),
	url('^bewegerinnen-wall/', views.avatar_wall),
    url('^account/edit$', views.profile_edit, name='profile_edit'),
    url('^account/edit$', views.profile_edit, name='profile_edit'),
    url(r"^account/login/$", views.LoginView.as_view(), name="account_signup"),
    url('^backoffice/mass_invite$', views.mass_invite, name='mass_invite'),
    url('^backoffice/export_results$', views.export_results, name='export_results'),
    url('^backoffice/download_csv/(?P<id>.*)$', views.download_csv, name='download_mass_invites'),
]