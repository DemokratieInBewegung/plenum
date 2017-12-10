from django.conf.urls import url
from django.views import generic
from . import views

urlpatterns = [
	# globals
    url('^$', views.index, name='home'),
    url('^user_autocomplete$', views.UserAutocomplete.as_view(), name='user_autocomplete'),
    url('^tag_autocomplete$', views.TagAutocomplete.as_view(), name='tag_autocomplete'),

    # initiative specifics
    url('^ueber/$', views.ueber, name="ueber"),
    url('^initiative/new$', views.new, name="new_initiative"),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/support$', views.support),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/ack_support$', views.ack_support),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/rm_support$', views.rm_support),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/edit$', views.edit),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/submit_to_committee$', views.submit_to_committee),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/new_argument$', views.new_argument),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/new_proposal$', views.new_proposal),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/new_moderation$', views.moderate),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/vote$', views.vote, name="vote"),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/reset_vote$', views.reset_vote, name="reset_vote"),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/compare/(?P<version_id>\d+)$', views.compare),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/invite/(?P<invite_type>.*)$', views.invite),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/add_tag$', views.add_tag),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/moderation/(?P<target_id>\d+)$', views.show_moderation),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/(?P<target_type>.*)/(?P<target_id>\d+)$', views.show_resp),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?$', views.item, name="initiative_item"),
    url('^comment/(?P<target_type>.*)/(?P<target_id>\d+)$', views.comment),
    url('^like/(?P<target_type>.*)/(?P<target_id>\d+)$', views.like),
    url('^unlike/(?P<target_type>.*)/(?P<target_id>\d+)$', views.unlike)
]