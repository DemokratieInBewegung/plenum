from django.conf.urls import url
from django.views import generic
from . import views

urlpatterns = [
	# globals
    url('^$', views.index, name='home'),
    url('^user_autocomplete$', views.UserAutocomplete.as_view(), name='user_autocomplete'),

    # initiative specifics
    url('^ueber/$', views.ueber, name="ueber"),
    url('^initiative/new$', views.edit, name="new_initiative"),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?$', views.item, name="initiative_item"),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/support$', views.support),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/ack_support$', views.ack_support),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/rm_support$', views.rm_support),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/publish$', views.publish),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/edit$', views.edit, name="edit_initiative"),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/new_argument$', views.new_argument),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/new_proposal$', views.new_proposal),
    url('^initiative/(?P<init_id>\d+)(?:-(?P<slug>.*))?/(?P<target_type>.*)/(?P<target_id>\d+)$', views.show_resp),
    url('^comment/(?P<target_type>.*)/(?P<target_id>\d+)$', views.comment),
    url('^like/(?P<target_type>.*)/(?P<target_id>\d+)$', views.like),
    url('^unlike/(?P<target_type>.*)/(?P<target_id>\d+)$', views.unlike)
]