from django.conf.urls import url
from django.views import generic
from . import views

urlpatterns = [
    url('^$', views.index),
    url('^initiative/(?P<init_id>\d+)$', views.item),
]