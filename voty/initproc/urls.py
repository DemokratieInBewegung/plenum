from django.conf.urls import url
from django.views import generic
from . import views

urlpatterns = [
	# globals
    url('^$', views.index, name='home'),
    url('^user_autocomplete$', views.UserAutocomplete.as_view(), name='user_autocomplete'),

    # initiative specifics
    url('^ueber/$', views.ueber, name="ueber"),
    url('^initiative/new$', views.new, name="new_initiative"),
    url('^initiative/(?P<init_id>\d+)$', views.item),
    url('^initiative/(?P<init_id>\d+)/support$', views.support),
    url('^initiative/(?P<init_id>\d+)/post_argument$', views.post_argument),
    url('^initiative/(?P<init_id>\d+)/(?P<arg_id>\d+)/like$', views.like_argument),
    url('^initiative/(?P<init_id>\d+)/(?P<arg_id>\d+)/unlike$', views.unlike_argument),
    url('^initiative/(?P<init_id>\d+)/(?P<arg_id>\d+)/post_comment$', views.post_comment)
]