from django.urls import path, re_path
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    re_path('^$',                             views.home,         name='home'),
    re_path('^nav/(?P<path>[\/0-9].*)$',      views.nav,          name='nav'),
    re_path('^entry/create/$',                views.entry_create, name='entry_create'),
    re_path('^entry/update/(?P<pk>[0-9]+)/$', views.entry_update, name='entry_update'),
]