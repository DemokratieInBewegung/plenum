from django.conf.urls import url, include
from django.views import generic
from . import views

urlpatterns = [
	# globals
    url('^$', views.index, name='home'),
    url('^agora$', views.agora, name='agora'),
    url('^thema/(?P<topic_id>\d+)(?:-(?P<slug>.*))?$', views.topic, name="topic"),
    url('^(?P<topic_id>\d+)(?:-(?P<slug>.*))?/beitrag/new$', views.new_contribution, name="new_contribution"),
    url('^initiative/new$', views.new, name="new_initiative"),
    url('^user_autocomplete$', views.UserAutocomplete.as_view(), name='user_autocomplete'),
    url(r'^su/', include('django_su.urls')),

    # initiative specifics
    url('^ueber/$', views.ueber, name="ueber"),
    url('^initiative/new$', views.new, name="new_initiative"),
    url(r'^(?P<initype>initiative|ao-aenderung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/support$', views.support),
    url(r'^(?P<initype>initiative|ao-aenderung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/ack_support$', views.ack_support),
    url(r'^(?P<initype>initiative|ao-aenderung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/rm_support$', views.rm_support),
    url(r'^(?P<initype>initiative|ao-aenderung|plenumsentscheidung|plenumsabwaegung|beitrag)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/edit$', views.edit),
    url(r'^(?P<initype>initiative|ao-aenderung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/submit_to_committee$', views.submit_to_committee),
    url(r'^(?P<initype>beitrag)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/new_question$', views.new_question),
    url(r'^(?P<initype>initiative|ao-aenderung|beitrag)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/new_argument$', views.new_argument),
    url(r'^(?P<initype>initiative|ao-aenderung|beitrag)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/new_proposal$', views.new_proposal),
    url(r'^(?P<initype>initiative|ao-aenderung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/new_moderation$', views.moderate),
    url(r'^(?P<initype>initiative|ao-aenderung|plenumsentscheidung|plenumsabwaegung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/vote$', views.vote, name="vote"),
    url(r'^(?P<initype>plenumsabwaegung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/preference$', views.preference, name="preference"),
    url(r'^(?P<initype>initiative|ao-aenderung|plenumsentscheidung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/reset_vote$', views.reset_vote, name="reset_vote"),
    url(r'^(?P<initype>plenumsabwaegung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/reset_preference$', views.reset_preference, name="reset_preference"),
    url(r'^(?P<initype>initiative|ao-aenderung|plenumsentscheidung|plenumsabwaegung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/compare/(?P<version_id>\d+)$', views.compare),
    url(r'^(?P<initype>initiative|ao-aenderung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/invite/(?P<invite_type>.*)$', views.invite),
    url(r'^(?P<initype>initiative|ao-aenderung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/moderation/(?P<target_id>\d+)$', views.show_moderation),
    url(r'^(?P<initype>initiative|ao-aenderung|beitrag)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/(?P<target_type>.*)/(?P<target_id>\d+)$', views.show_resp),
    url(r'^(?P<initype>initiative|ao-aenderung|plenumsentscheidung|plenumsabwaegung|beitrag)/(?P<init_id>\d+)(?:-(?P<slug>.*))?$', views.item, name="initiative_item"),
    url('^comment/(?P<target_type>.*)/(?P<target_id>\d+)$', views.comment),
    url('^like/(?P<target_type>.*)/(?P<target_id>\d+)$', views.like),
    url('^unlike/(?P<target_type>.*)/(?P<target_id>\d+)$', views.unlike),
    url('^ao-aenderung/new$', views.new_policychange, name="new_policychange"),
    url('^plenumsentscheidung/new$', views.new_plenumvote, name="new_plenumvote"),
    url('^plenumsabwaegung/new$', views.new_plenumoptions, name="new_plenumoptions"),
    url(r'^(?P<initype>ao-aenderung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/start_discussion_phase$', views.start_discussion_phase),
    url(r'^(?P<initype>beitrag)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/start_support_phase$', views.start_support_phase),
    url(r'^(?P<initype>plenumsentscheidung|plenumsabwaegung)/(?P<init_id>\d+)(?:-(?P<slug>.*))?/start_voting$', views.start_voting)

]
