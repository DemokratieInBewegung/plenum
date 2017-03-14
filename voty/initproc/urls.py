from django.conf.urls import url
from django.views import generic
from . import views

urlpatterns = [
    # url(r'^$', views.index, name='list'),
    # urlpatterns = [
    url('^$', generic.TemplateView.as_view(template_name="initproc/index.html"), name="index"),
]