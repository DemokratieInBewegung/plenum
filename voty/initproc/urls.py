from django.conf.urls import url
from django.views import generic
from . import views

urlpatterns = [
  url(r'^(?P<filename>(robots.txt)|(humans.txt))$', views.crawler, name='crawler'),

	# home/i18n
  url(r"^$", views.index, name="home"),

  # about (ueber) is not static
  url(r"^about/$", views.about, name="about"),
  url(r"^account/language/$", views.account_language, name="account_language"),

  # autocomplete for mass invitations  
  url(r"^user_autocomplete$", views.UserAutocomplete.as_view(), name="user_autocomplete"),

  # initiative
  url(r"^initiative/new$", views.new, name="new_initiative"),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/support$", views.support),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/ack_support$", views.ack_support),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/rm_support$", views.rm_support),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/edit$", views.edit),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/submit_to_committee$", views.submit_to_committee),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/new_argument$", views.new_argument),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/new_proposal$", views.new_proposal),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/new_moderation$", views.moderate),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/vote$", views.vote, name="vote"),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/reset_vote$", views.reset_vote, name="reset_vote"),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/compare/(?P<version_id>\d+)$", views.compare),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/invite/(?P<invite_type>.*)$", views.invite),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/moderation/(?P<target_id>\d+)$", views.show_moderation),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/(?P<target_type>.*)/(?P<target_id>\d+)$", views.show_resp),
  url(r"^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?$", views.item, name="initiative_item"),
  url(r"^comment/(?P<target_type>.*)/(?P<target_id>\d+)$", views.comment),
  url(r"^like/(?P<target_type>.*)/(?P<target_id>\d+)$", views.like),
  url(r"^unlike/(?P<target_type>.*)/(?P<target_id>\d+)$", views.unlike)
]
