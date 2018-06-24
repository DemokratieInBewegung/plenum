from django.conf.urls import url
from . import views

urlpatterns = [
  url(r"^account/edit$", views.profile_edit, name="profile_edit"),
  url(r"^account/login/$", views.LoginView.as_view(), name="account_signup"),
  url(r"^backoffice/download_csv/(?P<id>.*)$", views.download_csv, name="download_invited_users"),
  url(r"^backoffice/invite_users/", views.invite_users, name="invite_users"),
  url(r"^backoffice/active_users/", views.active_users, name="active_users"),
]
